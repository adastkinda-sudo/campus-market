from __future__ import annotations

import os
import re
from pathlib import Path

try:
    import pymysql
except ImportError:  # pragma: no cover - used to show a clearer runtime message.
    pymysql = None

import app as sqlite_app


BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = Path(__file__).resolve().parent / "schema_mysql.sql"

MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "123456")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "campus_market")
MYSQL_CHARSET = os.environ.get("MYSQL_CHARSET", "utf8mb4")
DATETIME_LOCAL_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?$")


class DictRow:
    def __init__(self, columns: list[str], row: tuple):
        self._columns = columns
        self._row = row

    def __getitem__(self, key):
        if isinstance(key, str):
            try:
                return self._row[self._columns.index(key)]
            except ValueError:
                raise KeyError(key)
        return self._row[key]

    def __getattr__(self, name: str):
        if name in self._columns:
            return self._row[self._columns.index(name)]
        raise AttributeError(name)

    def keys(self):
        return self._columns

    def __iter__(self):
        return iter(self._row)

    def __len__(self):
        return len(self._row)


class DictCursor:
    def __init__(self, cursor):
        self._cursor = cursor
        self.description = cursor.description

    def execute(self, sql, params=()):
        sql = translate_sql(sql)
        params = normalize_params(params)
        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)
        self.description = self._cursor.description
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        columns = [desc[0] for desc in self._cursor.description]
        return DictRow(columns, row)

    def fetchall(self):
        columns = [desc[0] for desc in self._cursor.description]
        return [DictRow(columns, row) for row in self._cursor.fetchall()]

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class DictConnection:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=()):
        cursor = self._conn.cursor()
        return DictCursor(cursor).execute(sql, params)

    def execute_raw(self, sql, params=()):
        cursor = self._conn.cursor()
        cursor.execute(sql, params or ())
        return cursor

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        return False


def require_pymysql():
    if pymysql is None:
        raise RuntimeError("缺少 PyMySQL，请先运行：python3 -m pip install -r requirements-mysql.txt")


def quote_identifier(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", identifier):
        raise ValueError(f"MySQL 标识符不安全：{identifier}")
    return f"`{identifier}`"


def raw_mysql_connection(database: str | None = MYSQL_DATABASE, autocommit: bool = False):
    require_pymysql()
    kwargs = {
        "host": MYSQL_HOST,
        "port": MYSQL_PORT,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
        "charset": MYSQL_CHARSET,
        "autocommit": autocommit,
    }
    if database:
        kwargs["database"] = database
    return pymysql.connect(**kwargs)


def connect():
    return DictConnection(raw_mysql_connection())


def translate_sql(sql: str) -> str:
    if sql.strip().upper() == "BEGIN IMMEDIATE":
        return "START TRANSACTION"
    sql = sql.replace("[User]", "`User`")
    sql = re.sub(r"\bdescription\b", "`description`", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bcondition\b", "`condition`", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bstatus\b", "`status`", sql, flags=re.IGNORECASE)
    return sql.replace("?", "%s")


def normalize_params(params):
    if params is None:
        return ()
    if not isinstance(params, (list, tuple)):
        return params
    return type(params)(normalize_param(value) for value in params)


def normalize_param(value):
    if isinstance(value, str) and DATETIME_LOCAL_RE.match(value):
        value = value.replace("T", " ")
        if len(value) == 16:
            value += ":00"
    return value


def split_mysql_script(script: str) -> list[str]:
    statements: list[str] = []
    delimiter = ";"
    buffer: list[str] = []

    for line in script.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        if stripped.upper().startswith("DELIMITER "):
            delimiter = stripped.split(None, 1)[1]
            continue

        buffer.append(line)
        current = "\n".join(buffer).rstrip()
        if current.endswith(delimiter):
            statements.append(current[: -len(delimiter)].strip())
            buffer = []

    trailing = "\n".join(buffer).strip()
    if trailing:
        statements.append(trailing)
    return [statement for statement in statements if statement]


def ensure_database() -> None:
    database = quote_identifier(MYSQL_DATABASE)
    with raw_mysql_connection(database=None, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {database} "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )


def execute_schema(conn: DictConnection) -> None:
    script = SCHEMA_PATH.read_text(encoding="utf-8")
    errors: list[str] = []
    for statement in split_mysql_script(script):
        try:
            conn.execute_raw(statement)
        except Exception as exc:
            errors.append(str(exc))
    conn.commit()
    if errors:
        # 如果是已知的表/列兼容性问题（如旧表缺少新列导致视图创建失败），
        # 只打印警告而不阻断启动，后续 ensure_mysql_migrations 会修复。
        print(f"[schema] {len(errors)} 条语句执行异常（将在迁移阶段修复）：")
        for err in errors:
            print(f"  - {err[:120]}")


def ensure_mysql_migrations(conn: DictConnection) -> None:
    user_profile_columns = [
        ("gender", "VARCHAR(10) DEFAULT '保密' AFTER wechat"),
        ("entryYear", "VARCHAR(20) AFTER gender"),
        ("avatarUrl", "VARCHAR(500) AFTER entryYear"),
        ("bio", "VARCHAR(300) AFTER avatarUrl"),
        ("campusCardImageUrl", "VARCHAR(500) AFTER bio"),
        ("authSubmitTime", "DATETIME AFTER campusCardImageUrl"),
    ]
    for column_name, column_sql in user_profile_columns:
        if not conn.execute(f"SHOW COLUMNS FROM `User` LIKE '{column_name}'").fetchone():
            conn.execute_raw(f"ALTER TABLE `User` ADD COLUMN {column_name} {column_sql}")

    campus_column = conn.execute("SHOW COLUMNS FROM Item LIKE 'campusName'").fetchone()
    if not campus_column:
        conn.execute_raw("ALTER TABLE Item ADD COLUMN campusName VARCHAR(20) NOT NULL DEFAULT '奉贤校区' AFTER categoryNo")
    campus_index = conn.execute("SHOW INDEX FROM Item WHERE Key_name = ?", ("idx_item_campus",)).fetchone()
    if not campus_index:
        conn.execute_raw("ALTER TABLE Item ADD INDEX idx_item_campus (campusName)")
    sqlite_app.core.apply_user_profile_defaults(conn)
    sqlite_app.core.apply_item_campus_defaults(conn)
    campus_check = conn.execute(
        """
        SELECT COUNT(*) AS n
        FROM information_schema.CHECK_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND CONSTRAINT_NAME = ?
        """,
        ("chk_item_campus",),
    ).fetchone()["n"]
    if not campus_check:
        conn.execute_raw("ALTER TABLE Item ADD CONSTRAINT chk_item_campus CHECK (campusName IN ('徐汇校区', '奉贤校区'))")
    sqlite_app.core.recreate_item_detail_view(conn)
    conn.commit()


def seed_mysql_market_data(conn: DictConnection) -> None:
    seller_student_nos = ("24010001", "24010002", "24010003", "24010004")

    def first_value(sql: str, params=()):
        row = conn.execute(sql, params).fetchone()
        return row[0] if row else None

    sellers: dict[str, int] = {}
    for student_no in seller_student_nos:
        user_no = first_value("SELECT userNo FROM [User] WHERE studentNo = ?", (student_no,))
        if user_no:
            sellers[student_no] = user_no
    if len(sellers) < 2:
        return

    admin_no = first_value("SELECT adminNo FROM Admin ORDER BY adminNo LIMIT 1")

    def remove_item(item_no: int) -> None:
        order_rows = conn.execute("SELECT orderNo FROM OrderSheet WHERE itemNo = ?", (item_no,)).fetchall()
        for order_row in order_rows:
            order_no = order_row[0]
            conn.execute("DELETE FROM Review WHERE orderNo = ?", (order_no,))
            conn.execute("DELETE FROM OrderSheet WHERE orderNo = ?", (order_no,))
        conn.execute("DELETE FROM Favorite WHERE itemNo = ?", (item_no,))
        conn.execute("DELETE FROM Message WHERE itemNo = ?", (item_no,))
        conn.execute("DELETE FROM Report WHERE targetType = '物品' AND targetNo = ?", (item_no,))
        conn.execute("DELETE FROM Item WHERE itemNo = ?", (item_no,))

    removed_seed_titles = (
        "测试",
        "测试1",
        "测试2",
        "测试商品",
        "22",
        "校园音乐节预售票一张",
        "全新防晒霜两支装",
        "食堂咖啡券 10 张",
        "网盘月卡会员兑换码",
    )
    item_ids_to_remove = {
        row[0]
        for row in conn.execute(
            """
            SELECT itemNo
            FROM Item
            WHERE title LIKE ?
               OR title IN (?, ?, ?, ?, ?, ?, ?, ?, ?)
               OR description IN (?, ?, ?, ?)
            """,
            ("测试%", *removed_seed_titles, "测试", "测试商品", "test", "TEST"),
        ).fetchall()
    }
    for item_no in sorted(item_ids_to_remove):
        remove_item(item_no)

    legacy_phone_rows = conn.execute("SELECT itemNo FROM Item WHERE title = ?", ("二手手机",)).fetchall()
    formal_phone_title = "Redmi K60 12G 256G"
    if legacy_phone_rows:
        if first_value("SELECT COUNT(*) FROM Item WHERE title = ?", (formal_phone_title,)):
            for row in legacy_phone_rows:
                remove_item(row[0])
        else:
            conn.execute("UPDATE Item SET title = ? WHERE itemNo = ?", (formal_phone_title, legacy_phone_rows[0][0]))
            for row in legacy_phone_rows[1:]:
                remove_item(row[0])

    conn.execute(
        """
        DELETE FROM Wanted
        WHERE title LIKE ?
           OR title IN (?, ?, ?)
           OR description IN (?, ?, ?, ?)
        """,
        ("测试%", "测试", "求购测试", "测试求购", "测试", "测试求购", "test", "TEST"),
    )

    if admin_no:
        conn.execute(
            """
            DELETE FROM Announcement
            WHERE title LIKE ?
               OR content LIKE ?
               OR title IN (?, ?, ?, ?, ?)
               OR content LIKE ?
            """,
            (
                "%测试%",
                "%测试%",
                "一条公告测试",
                "平台试运行公告",
                "毕业季二手交易提醒",
                "贵重数码物品面交验机提醒",
                "期末教材与复习资料交易提示",
                "%数据库原理实验演示%",
            ),
        )

        official_announcements = [
            (
                "华东理工大学校园二手交易平台公告",
                "本平台面向华东理工大学徐汇校区、奉贤校区学生、教职工与校友，支持教材资料、数码设备、宿舍用品、代步工具等校内闲置物品流转。",
            ),
            (
                "两校区线下面交安全提醒",
                "下单时只需先确认徐汇校区或奉贤校区，具体地点由买卖双方通过私聊确认；贵重物品建议选择校内公共区域当面验收。",
            ),
            (
                "毕业季教材与宿舍用品流转提醒",
                "毕业季前后，华东理工大学两校区教材、复习资料、床帘支架、收纳用品和自行车交易较多，发布时请写清校区、成色和配件情况，具体交接点通过私聊确认。",
            ),
        ]
        for title, content in official_announcements:
            announcement_no = first_value("SELECT announcementNo FROM Announcement WHERE title = ?", (title,))
            if announcement_no:
                conn.execute(
                    "UPDATE Announcement SET content = ? WHERE announcementNo = ?",
                    (content, announcement_no),
                )
                continue
            conn.execute(
                "INSERT INTO Announcement(adminNo, title, content) VALUES (?, ?, ?)",
                (admin_no, title, content),
            )

    def ensure_location(campus_name: str, location_name: str) -> int:
        location_no = first_value(
            "SELECT locationNo FROM Location WHERE campusName = ? AND locationName = ?",
            (campus_name, location_name),
        )
        if location_no:
            return location_no
        conn.execute(
            "INSERT INTO Location(locationName, campusName) VALUES (?, ?)",
            (location_name, campus_name),
        )
        return first_value(
            "SELECT locationNo FROM Location WHERE campusName = ? AND locationName = ?",
            (campus_name, location_name),
        )

    official_locations = [
        ("徐汇校区", "具体地点私聊确定"),
        ("奉贤校区", "具体地点私聊确定"),
    ]
    official_location_ids = {
        (campus_name, location_name): ensure_location(campus_name, location_name)
        for campus_name, location_name in official_locations
    }

    legacy_location_map = {
        ("主校区", "南门"): ("奉贤校区", "具体地点私聊确定"),
        ("主校区", "一食堂门口"): ("奉贤校区", "具体地点私聊确定"),
        ("主校区", "图书馆北门"): ("徐汇校区", "具体地点私聊确定"),
        ("主校区", "信息楼大厅"): ("奉贤校区", "具体地点私聊确定"),
        ("东校区", "东区宿舍楼下"): ("奉贤校区", "具体地点私聊确定"),
    }
    allowed_campuses = {"徐汇校区", "奉贤校区"}
    location_rows = conn.execute("SELECT locationNo, locationName, campusName FROM Location").fetchall()
    for row in location_rows:
        location_no = row["locationNo"]
        location_name = row["locationName"]
        campus_name = row["campusName"]
        if campus_name in allowed_campuses and (campus_name, location_name) in official_location_ids:
            continue

        target = legacy_location_map.get((campus_name, location_name))
        if not target:
            if campus_name == "徐汇校区":
                target = ("徐汇校区", "具体地点私聊确定")
            elif campus_name == "奉贤校区":
                target = ("奉贤校区", "具体地点私聊确定")
            elif "徐汇" in campus_name or "徐汇" in location_name:
                target = ("徐汇校区", "具体地点私聊确定")
            else:
                target = ("奉贤校区", "具体地点私聊确定")

        target_no = official_location_ids.get(target) or ensure_location(*target)
        if location_no != target_no:
            conn.execute("UPDATE OrderSheet SET locationNo = ? WHERE locationNo = ?", (target_no, location_no))
            conn.execute("DELETE FROM Location WHERE locationNo = ?", (location_no,))

    def delete_category_if_unused(name: str) -> None:
        rows = conn.execute("SELECT categoryNo FROM Category WHERE categoryName = ?", (name,)).fetchall()
        for row in rows:
            category_no = row[0]
            item_count = first_value("SELECT COUNT(*) FROM Item WHERE categoryNo = ?", (category_no,))
            wanted_count = first_value("SELECT COUNT(*) FROM Wanted WHERE categoryNo = ?", (category_no,))
            child_count = first_value("SELECT COUNT(*) FROM Category WHERE parentCategoryNo = ?", (category_no,))
            if not item_count and not wanted_count and not child_count:
                conn.execute("DELETE FROM Category WHERE categoryNo = ?", (category_no,))

    for category_name in ("演出票券", "护肤彩妆", "校园卡券", "会员订阅", "票券卡券", "其他类型"):
        delete_category_if_unused(category_name)

    def ensure_category(name: str, parent_name: str | None = None) -> int:
        parent_no = category_ids.get(parent_name) if parent_name else None
        category_no = first_value(
            """
            SELECT categoryNo
            FROM Category
            WHERE categoryName = ?
              AND ((parentCategoryNo = ?) OR (parentCategoryNo IS NULL AND ? IS NULL))
            """,
            (name, parent_no, parent_no),
        )
        if category_no:
            return category_no
        conn.execute(
            "INSERT INTO Category(categoryName, parentCategoryNo) VALUES (?, ?)",
            (name, parent_no),
        )
        return first_value(
            """
            SELECT categoryNo
            FROM Category
            WHERE categoryName = ?
              AND ((parentCategoryNo = ?) OR (parentCategoryNo IS NULL AND ? IS NULL))
            """,
            (name, parent_no, parent_no),
        )

    categories = [
        ("书籍教材", None),
        ("专业课教材", "书籍教材"),
        ("考试资料", "书籍教材"),
        ("公共课教材", "书籍教材"),
        ("考研资料", "书籍教材"),
        ("文学读物", "书籍教材"),
        ("外语学习", "书籍教材"),
        ("学习办公", None),
        ("文具用品", "学习办公"),
        ("实验耗材", "学习办公"),
        ("办公设备", "学习办公"),
        ("数码产品", None),
        ("手机平板", "数码产品"),
        ("电脑配件", "数码产品"),
        ("电脑整机", "数码产品"),
        ("电子阅读器", "数码产品"),
        ("音频设备", "数码产品"),
        ("摄影器材", "数码产品"),
        ("生活用品", None),
        ("宿舍电器", "生活用品"),
        ("收纳清洁", "生活用品"),
        ("床品家纺", "生活用品"),
        ("厨具餐具", "生活用品"),
        ("家居装饰", "生活用品"),
        ("代步工具", None),
        ("自行车", "代步工具"),
        ("滑板轮滑", "代步工具"),
        ("骑行配件", "代步工具"),
        ("运动户外", None),
        ("健身器材", "运动户外"),
        ("球类用品", "运动户外"),
        ("户外露营", "运动户外"),
        ("乐器文娱", None),
        ("乐器", "乐器文娱"),
        ("桌游手办", "乐器文娱"),
        ("美妆服饰", None),
        ("服装鞋帽", "美妆服饰"),
        ("箱包配饰", "美妆服饰"),
        ("美妆个护", "美妆服饰"),
        ("饰品手表", "美妆服饰"),
    ]
    category_ids: dict[str, int] = {}
    for name, parent_name in categories:
        category_ids[name] = ensure_category(name, parent_name)

    def migrate_legacy_category(source_name: str, target_name: str, source_parent_name: str | None = None) -> None:
        target_no = category_ids.get(target_name)
        if not target_no:
            return
        source_rows = conn.execute(
            """
            SELECT c.categoryNo
            FROM Category c
            LEFT JOIN Category pc ON pc.categoryNo = c.parentCategoryNo
            WHERE c.categoryName = ?
              AND (
                    (? IS NULL AND c.parentCategoryNo IS NULL)
                 OR pc.categoryName = ?
              )
            """,
            (source_name, source_parent_name, source_parent_name),
        ).fetchall()
        for row in source_rows:
            source_no = row[0]
            if source_no == target_no:
                continue
            conn.execute("UPDATE Item SET categoryNo = ? WHERE categoryNo = ?", (target_no, source_no))
            conn.execute("UPDATE Wanted SET categoryNo = ? WHERE categoryNo = ?", (target_no, source_no))

    migrate_legacy_category("专业课教材", "专业课教材", "书籍")
    migrate_legacy_category("考试资料", "考试资料", "书籍")
    migrate_legacy_category("书籍", "专业课教材")
    for category_name in ("专业课教材", "考试资料", "书籍", "其他类型"):
        delete_category_if_unused(category_name)

    items = [
        ("24010001", "公共课教材", "高等数学同济第七版上下册", "公共课教材两册合售，重点章节有荧光笔标记，适合期末复习。", 96, 38, "八成新", "/assets/book.svg", 132),
        ("24010002", "公共课教材", "线性代数辅导讲义", "配套例题和课后题解析比较完整，封面有轻微折痕。", 45, 18, "八成新", "/assets/book.svg", 86),
        ("24010003", "考研资料", "考研数学一复习全套资料", "包含基础讲义、强化题册和错题贴纸，适合暑期开始系统复习。", 188, 72, "九成新", "/assets/book.svg", 210),
        ("24010004", "考研资料", "计算机408真题解析", "按年份整理，数据结构和组成原理部分标注较多。", 89, 36, "八成新", "/assets/book.svg", 174),
        ("24010001", "外语学习", "雅思核心词汇与听力练习册", "词汇书几乎全新，听力练习册做了前两章。", 78, 29, "九成新", "/assets/book.svg", 61),
        ("24010002", "文学读物", "三体全集纪念版", "三册套装，书脊完整，适合收藏或假期阅读。", 168, 68, "九成新", "/assets/book.svg", 145),
        ("24010003", "专业课教材", "化工原理课程设计资料包", "含课程设计说明书、往年习题和计算表格模板，适合复习参考。", 82, 30, "八成新", "/assets/book.svg", 128),
        ("24010004", "考试资料", "六级冲刺作文翻译讲义", "按题型整理范文和高频表达，附听力错题记录。", 56, 20, "九成新", "/assets/book.svg", 102),
        ("24010001", "文具用品", "晨光文具整理套装", "含文件袋、便利贴、索引贴和中性笔，搬宿舍整理出来的备用文具。", 42, 16, "九成新", "/assets/kettle.svg", 73),
        ("24010002", "文具用品", "得力 A4 文件夹资料盒", "三只资料盒加十个透明文件袋，适合整理实验报告和复习资料。", 39, 14, "八成新", "/assets/kettle.svg", 66),
        ("24010003", "实验耗材", "实验白大褂与防护镜套装", "白大褂 M 码，防护镜镜片清晰，适合实验课备用。", 98, 38, "八成新", "/assets/kettle.svg", 117),
        ("24010004", "实验耗材", "电子实验面包板套件", "含面包板、杜邦线、电阻电容和 LED，适合电路实验入门。", 86, 32, "九成新", "/assets/laptop.svg", 91),
        ("24010001", "办公设备", "罗技高清网课摄像头", "1080P 摄像头，麦克风正常，适合线上面试和网课。", 189, 75, "八成新", "/assets/laptop.svg", 139),
        ("24010002", "办公设备", "惠普小型喷墨打印机", "黑白和彩色打印正常，适合宿舍打印资料，墨量剩余约一半。", 699, 260, "七成新", "/assets/laptop.svg", 205),
        ("24010003", "电脑整机", "ThinkPad X1 Carbon 备用机", "i5/16G/512G，电池健康良好，适合论文写作和轻办公。", 6800, 2980, "八成新", "/assets/laptop.svg", 320),
        ("24010001", "电脑整机", "MacBook Air M1 8G 256G", "日常上课和编程够用，外壳有轻微使用痕迹，带原装充电器。", 7999, 3850, "八成新", "/assets/laptop.svg", 288),
        ("24010002", "电脑配件", "27 英寸 2K 显示器", "屏幕无坏点，支架可升降，适合宿舍桌面扩展。", 1099, 520, "九成新", "/assets/laptop.svg", 236),
        ("24010004", "电脑配件", "移动固态硬盘 1TB", "USB-C 接口，读写正常，送收纳袋。", 599, 265, "九成新", "/assets/laptop.svg", 198),
        ("24010003", "电脑配件", "罗技 MX Master 2S 鼠标", "滚轮和侧键正常，适合长时间写论文和做图表。", 499, 160, "八成新", "/assets/laptop.svg", 172),
        ("24010001", "手机平板", "iPhone 13 128G 蓝色", "国行，电池健康 88%，屏幕和摄像头正常，带透明壳。", 5999, 2650, "八成新", "/assets/laptop.svg", 355),
        ("24010003", "手机平板", "Redmi K60 12G 256G", "屏幕和电池状态正常，机身有轻微使用痕迹，适合作为备用机或日常上课使用。", 2499, 980, "八成新", "/assets/laptop.svg", 147),
        ("24010003", "手机平板", "小米平板 6 配键盘壳", "适合看网课和记笔记，键盘壳连接稳定。", 2299, 1180, "九成新", "/assets/laptop.svg", 167),
        ("24010004", "电子阅读器", "Kindle Paperwhite 4 电子书", "屏幕无亮点，背光正常，适合通勤阅读和看英文原版。", 998, 360, "八成新", "/assets/laptop.svg", 158),
        ("24010002", "音频设备", "Sony WH-1000XM4 降噪耳机", "降噪和续航正常，耳罩已更换，适合自习室使用。", 2299, 860, "八成新", "/assets/laptop.svg", 249),
        ("24010004", "音频设备", "JBL 便携蓝牙音箱", "音质正常，户外活动和宿舍聚会可用。", 399, 145, "七成新", "/assets/laptop.svg", 93),
        ("24010003", "摄影器材", "佳能微单定焦镜头 50mm", "镜片无霉无划痕，适合社团摄影和人像练习。", 899, 430, "八成新", "/assets/laptop.svg", 121),
        ("24010001", "摄影器材", "富士拍立得 Mini 11", "成像正常，外壳有轻微磨痕，适合社团活动记录。", 599, 238, "八成新", "/assets/laptop.svg", 96),
        ("24010004", "宿舍电器", "迷你电饭煲 1.2L", "宿舍低功率款，内胆无明显划痕，适合一人食。", 169, 62, "八成新", "/assets/kettle.svg", 112),
        ("24010001", "宿舍电器", "小型空气循环扇", "三档风速，夏天宿舍桌面使用方便。", 129, 46, "八成新", "/assets/kettle.svg", 76),
        ("24010003", "宿舍电器", "折叠电热水壶", "旅行和宿舍都能用，烧水正常，收纳体积小。", 119, 42, "八成新", "/assets/kettle.svg", 84),
        ("24010002", "收纳清洁", "真空压缩袋八件套", "搬宿舍剩余物品，大中小号都有，未使用。", 49, 19, "全新", "/assets/kettle.svg", 58),
        ("24010004", "收纳清洁", "宿舍桌面置物架", "双层金属置物架，适合放书本、护肤品和小电器。", 79, 28, "八成新", "/assets/kettle.svg", 141),
        ("24010003", "床品家纺", "床帘支架与遮光帘套装", "适配上床下桌，支架完整，遮光效果好。", 158, 60, "八成新", "/assets/kettle.svg", 104),
        ("24010001", "床品家纺", "乳胶枕和枕套组合", "枕套已清洗，乳胶枕支撑较好，适合颈椎不舒服的同学。", 229, 78, "八成新", "/assets/kettle.svg", 52),
        ("24010004", "厨具餐具", "便携咖啡手冲套装", "滤杯、分享壶和手摇磨豆机一套，适合宿舍咖啡入门。", 268, 98, "八成新", "/assets/kettle.svg", 83),
        ("24010002", "厨具餐具", "不锈钢保温饭盒两层", "密封正常，适合带饭或水果，已清洗消毒。", 89, 30, "八成新", "/assets/kettle.svg", 45),
        ("24010003", "家居装饰", "ins 风桌面小台历摆件", "桌面摆件和台历套装，适合宿舍书桌装饰。", 45, 15, "九成新", "/assets/kettle.svg", 38),
        ("24010004", "家居装饰", "落地衣帽架", "金属衣帽架，底座稳定，适合宿舍门口挂外套和包。", 129, 50, "八成新", "/assets/kettle.svg", 69),
        ("24010001", "自行车", "捷安特山地车 ATX", "变速顺畅，刹车已调校，支持私聊约定看车时间。", 1599, 690, "七成新", "/assets/bicycle.svg", 275),
        ("24010002", "自行车", "永久城市通勤自行车", "带车筐和后货架，适合校内通勤。", 599, 220, "八成新", "/assets/bicycle.svg", 190),
        ("24010003", "滑板轮滑", "双翘滑板入门款", "板面有正常磨损，桥和轮子状态良好。", 299, 95, "七成新", "/assets/bicycle.svg", 118),
        ("24010001", "滑板轮滑", "成人轮滑鞋 39 码", "轮子顺滑，护具齐全，适合校园广场练习。", 399, 138, "七成新", "/assets/bicycle.svg", 77),
        ("24010004", "骑行配件", "自行车头盔和车灯套装", "头盔 M 码，前后灯可充电，夜骑更安全。", 188, 70, "八成新", "/assets/bicycle.svg", 89),
        ("24010003", "骑行配件", "自行车车锁与铃铛套装", "车锁、铃铛和反光贴一套，适合校内通勤车补齐配件。", 35, 10, "七成新", "/assets/bicycle.svg", 57),
        ("24010001", "健身器材", "可调节哑铃一对 10kg", "重量片齐全，适合宿舍基础力量训练。", 299, 128, "八成新", "/assets/kettle.svg", 151),
        ("24010004", "健身器材", "瑜伽垫加拉力带", "瑜伽垫厚度 8mm，拉力带两条，适合宿舍拉伸。", 128, 45, "九成新", "/assets/kettle.svg", 93),
        ("24010002", "球类用品", "李宁羽毛球拍双拍套装", "两支拍加拍包，线和手胶状态良好。", 398, 158, "八成新", "/assets/kettle.svg", 169),
        ("24010003", "球类用品", "乒乓球拍成品双拍", "两支成品拍加三星球一盒，适合体育课和社团活动。", 158, 58, "八成新", "/assets/kettle.svg", 118),
        ("24010003", "户外露营", "折叠露营椅两把", "社团活动用过几次，收纳袋齐全。", 238, 88, "八成新", "/assets/kettle.svg", 74),
        ("24010001", "户外露营", "轻量野餐垫 2m", "防潮野餐垫，适合草坪活动和社团团建。", 99, 35, "九成新", "/assets/kettle.svg", 59),
        ("24010004", "乐器", "入门民谣吉他 41 寸", "琴弦刚换，适合零基础练习，附琴包。", 599, 230, "七成新", "/assets/kettle.svg", 178),
        ("24010001", "乐器", "卡林巴拇指琴 17 音", "音准正常，附教程谱和调音锤。", 129, 45, "九成新", "/assets/kettle.svg", 64),
        ("24010002", "乐器", "尤克里里 23 寸", "桃花芯木面板，弦距适中，适合宿舍弹唱入门。", 268, 96, "八成新", "/assets/kettle.svg", 116),
        ("24010002", "桌游手办", "狼人杀与 UNO 桌游套装", "社团团建用过，卡牌齐全。", 118, 39, "八成新", "/assets/kettle.svg", 135),
        ("24010003", "桌游手办", "海贼王小手办三件套", "摆柜展示过，无缺件，适合桌面装饰。", 169, 60, "八成新", "/assets/kettle.svg", 82),
        ("24010004", "服装鞋帽", "毕业季正装西服外套", "男款 L 码，只穿过一次答辩，适合面试。", 599, 168, "九成新", "/assets/kettle.svg", 97),
        ("24010002", "服装鞋帽", "Nike 跑步鞋 42 码", "鞋底磨损较轻，适合日常慢跑和体育课。", 699, 220, "八成新", "/assets/kettle.svg", 144),
        ("24010001", "箱包配饰", "新秀丽双肩电脑包", "可放 15.6 英寸电脑，背带和拉链完好。", 699, 210, "八成新", "/assets/kettle.svg", 182),
        ("24010003", "箱包配饰", "20 寸登机行李箱", "拉杆和轮子顺滑，适合短途出行或回家。", 399, 145, "八成新", "/assets/kettle.svg", 130),
        ("24010004", "美妆个护", "便携带灯化妆镜", "三档亮度，Type-C 充电，宿舍桌面使用方便。", 99, 36, "九成新", "/assets/kettle.svg", 72),
        ("24010001", "美妆个护", "负离子卷发棒", "升温正常，带隔热收纳袋，适合毕业照造型。", 199, 68, "八成新", "/assets/kettle.svg", 86),
        ("24010002", "饰品手表", "卡西欧学生电子表", "表带完整，计时和闹钟功能正常。", 269, 95, "八成新", "/assets/kettle.svg", 101),
        ("24010003", "饰品手表", "简约银色项链", "戴过两次，包装盒还在，适合日常搭配。", 128, 45, "九成新", "/assets/kettle.svg", 63),
    ]

    for seller_student_no, category_name, title, description, original, sell, condition, image, views in items:
        if seller_student_no not in sellers or category_name not in category_ids:
            continue
        campus_name = sqlite_app.core.infer_item_campus(title, category_name)
        image_url = image
        if image_url in sqlite_app.core.GENERIC_PRODUCT_IMAGES:
            image_url = sqlite_app.core.default_image_for_category_text(f"{title} {category_name}")
        if first_value("SELECT COUNT(*) FROM Item WHERE title = ?", (title,)):
            conn.execute(
                """
                UPDATE Item
                   SET sellerNo = ?, categoryNo = ?, campusName = ?, description = ?,
                       originalPrice = ?, sellPrice = ?, condition = ?, imageUrl = ?, viewCount = ?
                 WHERE title = ?
                """,
                (
                    sellers[seller_student_no],
                    category_ids[category_name],
                    campus_name,
                    description,
                    original,
                    sell,
                    condition,
                    image_url,
                    views,
                    title,
                ),
            )
            continue
        conn.execute(
            """
            INSERT INTO Item(sellerNo, categoryNo, campusName, title, description, originalPrice, sellPrice, condition, imageUrl, viewCount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sellers[seller_student_no],
                category_ids[category_name],
                campus_name,
                title,
                description,
                original,
                sell,
                condition,
                image_url,
                views,
            ),
        )

    generic_images = tuple(sorted(sqlite_app.core.GENERIC_PRODUCT_IMAGES))
    placeholders = ", ".join(["?"] * len(generic_images))
    generic_image_rows = conn.execute(
        f"""
        SELECT i.itemNo, i.title, i.imageUrl, c.categoryName, pc.categoryName AS parentCategoryName
        FROM Item i
        JOIN Category c ON c.categoryNo = i.categoryNo
        LEFT JOIN Category pc ON pc.categoryNo = c.parentCategoryNo
        WHERE i.imageUrl IN ({placeholders})
        """,
        generic_images,
    ).fetchall()
    for row in generic_image_rows:
        image_text = f"{row['title']} {row['categoryName']} {row['parentCategoryName'] or ''}"
        image_url = sqlite_app.core.default_image_for_category_text(image_text)
        if image_url != row["imageUrl"]:
            conn.execute("UPDATE Item SET imageUrl = ? WHERE itemNo = ?", (image_url, row["itemNo"]))

    wanted_posts = [
        (
            "24010002",
            "考研资料",
            "求购考研数学一强化讲义",
            "希望是近两年的讲义或题册，最好有章节重点和错题标记，徐汇校区或奉贤校区均可，具体地点私聊确认。",
            60,
        ),
        (
            "24010001",
            "电脑配件",
            "求购二手显示器或升降支架",
            "奉贤校区宿舍桌面学习使用，显示器希望 24 英寸以上，支架要求升降顺畅。",
            450,
        ),
        (
            "24010004",
            "床品家纺",
            "求购上床下桌床帘支架",
            "需要完整支架和挂钩，奉贤校区交易优先，具体地点私聊确认。",
            55,
        ),
        (
            "24010003",
            "专业课教材",
            "求购化工原理或物化教材",
            "希望是近两年课程使用版本，有实验课笔记或重点标注更好。",
            45,
        ),
        (
            "24010001",
            "电子阅读器",
            "求购 Kindle 或其他电纸书",
            "屏幕正常即可，主要用于通勤看英文原版和论文资料。",
            300,
        ),
        (
            "24010002",
            "实验耗材",
            "求购实验白大褂 S 码",
            "希望白大褂干净完整，防护镜可一起打包。",
            35,
        ),
        (
            "24010004",
            "球类用品",
            "求购乒乓球拍或羽毛球拍",
            "体育课和社团活动使用，成色七成新以上即可。",
            80,
        ),
        (
            "24010001",
            "家居装饰",
            "求购宿舍落地衣帽架",
            "需要底座稳定、不占空间，奉贤校区优先。",
            45,
        ),
        (
            "24010003",
            "箱包配饰",
            "求购 20 寸左右行李箱",
            "拉杆和轮子顺畅即可，暑假回家使用。",
            120,
        ),
        (
            "24010002",
            "乐器",
            "求购尤克里里或入门吉他",
            "想零基础练习弹唱，希望附调音器或教材。",
            120,
        ),
    ]
    for buyer_student_no, category_name, title, description, expected_price in wanted_posts:
        if buyer_student_no not in sellers or category_name not in category_ids:
            continue
        wanted_no = first_value("SELECT wantedNo FROM Wanted WHERE title = ?", (title,))
        if wanted_no:
            conn.execute(
                """
                UPDATE Wanted
                   SET categoryNo = ?, description = ?, expectedPrice = ?
                 WHERE wantedNo = ?
                """,
                (category_ids[category_name], description, expected_price, wanted_no),
            )
            continue
        conn.execute(
            """
            INSERT INTO Wanted(buyerNo, categoryNo, title, description, expectedPrice)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sellers[buyer_student_no], category_ids[category_name], title, description, expected_price),
        )

    def item_no_by_title(title: str) -> int | None:
        return first_value("SELECT itemNo FROM Item WHERE title = ?", (title,))

    def ensure_favorite(student_no: str, title: str) -> None:
        user_no = sellers.get(student_no)
        item_no = item_no_by_title(title)
        if not user_no or not item_no:
            return
        if first_value("SELECT COUNT(*) FROM Favorite WHERE userNo = ? AND itemNo = ?", (user_no, item_no)):
            return
        conn.execute("INSERT INTO Favorite(userNo, itemNo) VALUES (?, ?)", (user_no, item_no))

    favorite_pairs = [
        ("24010002", "MacBook Air M1 8G 256G"),
        ("24010003", "MacBook Air M1 8G 256G"),
        ("24010004", "iPhone 13 128G 蓝色"),
        ("24010001", "Sony WH-1000XM4 降噪耳机"),
        ("24010002", "ThinkPad X1 Carbon 备用机"),
        ("24010001", "Kindle Paperwhite 4 电子书"),
        ("24010004", "惠普小型喷墨打印机"),
        ("24010003", "实验白大褂与防护镜套装"),
        ("24010002", "捷安特山地车 ATX"),
        ("24010004", "李宁羽毛球拍双拍套装"),
        ("24010001", "入门民谣吉他 41 寸"),
        ("24010003", "20 寸登机行李箱"),
        ("24010002", "负离子卷发棒"),
        ("24010004", "卡西欧学生电子表"),
    ]
    for student_no, title in favorite_pairs:
        ensure_favorite(student_no, title)

    def ensure_message(title: str, student_no: str, content: str, parent_message_no: int | None = None) -> int | None:
        user_no = sellers.get(student_no)
        item_no = item_no_by_title(title)
        if not user_no or not item_no:
            return None
        existing_no = first_value(
            """
            SELECT messageNo
            FROM Message
            WHERE itemNo = ? AND userNo = ? AND content = ?
            ORDER BY messageNo
            LIMIT 1
            """,
            (item_no, user_no, content),
        )
        if existing_no:
            return existing_no
        conn.execute(
            "INSERT INTO Message(itemNo, userNo, content, parentMessageNo) VALUES (?, ?, ?, ?)",
            (item_no, user_no, content, parent_message_no),
        )
        return first_value(
            """
            SELECT messageNo
            FROM Message
            WHERE itemNo = ? AND userNo = ? AND content = ?
            ORDER BY messageNo DESC
            LIMIT 1
            """,
            (item_no, user_no, content),
        )

    message_threads = [
        ("Kindle Paperwhite 4 电子书", "24010001", "请问原装数据线还在吗？", "24010004", "数据线还在，保护套也可以一起给。"),
        ("惠普小型喷墨打印机", "24010003", "能现场试打一页吗？", "24010002", "可以，私聊约时间后带一张测试纸。"),
        ("实验白大褂与防护镜套装", "24010002", "白大褂适合 160 左右身高吗？", "24010003", "M 码偏宽松，160 到 170 都可以穿。"),
        ("捷安特山地车 ATX", "24010004", "周末能在奉贤校区看车吗？", "24010001", "可以，具体地点私聊确认。"),
        ("入门民谣吉他 41 寸", "24010001", "弦距高不高，适合新手吗？", "24010004", "弦距已经调过，新手按起来不会太吃力。"),
        ("20 寸登机行李箱", "24010001", "箱体有没有裂纹？", "24010003", "没有裂纹，主要是外壳有几处正常划痕。"),
        ("卡西欧学生电子表", "24010003", "电池最近换过吗？", "24010002", "上个月刚换，正常用应该还能撑很久。"),
    ]
    for title, ask_student_no, question, reply_student_no, reply in message_threads:
        parent_no = ensure_message(title, ask_student_no, question)
        ensure_message(title, reply_student_no, reply, parent_no)


def init_db() -> None:
    ensure_database()
    conn = connect()
    try:
        execute_schema(conn)
        # 补全旧表可能缺失的列，然后重建视图
        ensure_mysql_migrations(conn)
        sqlite_app.core.recreate_item_detail_view(conn)
        sqlite_app.seed_db(conn)
        seed_mysql_market_data(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def is_integrity_error(exc: Exception) -> bool:
    if pymysql is None:
        return False
    if isinstance(exc, pymysql.err.IntegrityError):
        return True
    if isinstance(exc, pymysql.err.OperationalError):
        error_code = exc.args[0] if exc.args else None
        return error_code in {1644, 3819}
    return False


sqlite_app.connect = connect
sqlite_app.init_db = init_db
sqlite_app.is_integrity_error = is_integrity_error
sqlite_app.SCHEMA_PATH = SCHEMA_PATH
sqlite_app.core.connect = connect
sqlite_app.core.init_db = init_db
sqlite_app.core.is_integrity_error = is_integrity_error
sqlite_app.core.SCHEMA_PATH = SCHEMA_PATH
sqlite_app.server.connect = connect
sqlite_app.server.init_db = init_db
sqlite_app.server.is_integrity_error = is_integrity_error


def main():
    init_db()
    host = os.environ.get("CAMPUS_MARKET_HOST", "127.0.0.1")
    port = int(os.environ.get("CAMPUS_MARKET_PORT", "8001"))
    server = sqlite_app.ThreadingHTTPServer((host, port), sqlite_app.CampusMarketHandler)
    print(f"华东理工大学校园二手交易系统 MySQL 版已启动：http://{host}:{port}")
    print("演示账号：管理员 admin/admin123；用户 24010001/123456、24010002/123456")
    server.serve_forever()


if __name__ == "__main__":
    main()
