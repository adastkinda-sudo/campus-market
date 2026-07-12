from __future__ import annotations

import hashlib
import sqlite3
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "campus_market.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
USER_TYPES = {"学生", "教职工", "校友"}
ECUST_CAMPUSES = {"徐汇校区", "奉贤校区"}
GENERIC_PRODUCT_IMAGES = {
    "/assets/book.svg",
    "/assets/laptop.svg",
    "/assets/bicycle.svg",
    "/assets/kettle.svg",
}
DEFAULT_AVATAR_URL = "/assets/default-avatar.svg"
SQLITE_LOCAL_TIME_MIGRATION_VERSION = 1
SQLITE_LOCAL_TIME_TRIGGER_COLUMNS = (
    ("Admin", "adminNo", "createdTime"),
    ("User", "userNo", "registerTime"),
    ("Announcement", "announcementNo", "publishTime"),
    ("Notification", "notificationNo", "createTime"),
    ("Item", "itemNo", "publishTime"),
    ("Favorite", "favoriteNo", "createTime"),
    ("Wanted", "wantedNo", "publishTime"),
    ("OrderSheet", "orderNo", "createTime"),
    ("Message", "messageNo", "msgTime"),
    ("PrivateConversation", "conversationNo", "createTime"),
    ("PrivateConversation", "conversationNo", "updateTime"),
    ("PrivateMessage", "privateMessageNo", "sendTime"),
    ("Review", "reviewNo", "reviewTime"),
    ("Report", "reportNo", "createTime"),
    ("Feedback", "feedbackNo", "createTime"),
)
SQLITE_UTC_HISTORY_COLUMNS = tuple(
    (table_name, column_name)
    for table_name, _, column_name in SQLITE_LOCAL_TIME_TRIGGER_COLUMNS
    if not (table_name == "PrivateConversation" and column_name == "updateTime")
)
CATEGORY_IMAGE_RULES = [
    (("电子阅读器", "kindle", "电纸书"), "/assets/ereader.svg"),
    (("手机平板", "手机", "平板", "iphone", "ipad", "redmi"), "/assets/phone.svg"),
    (("音频设备", "耳机", "音箱", "蓝牙"), "/assets/audio.svg"),
    (("摄影器材", "相机", "镜头", "拍立得", "摄像头"), "/assets/camera.svg"),
    (("打印机", "办公设备"), "/assets/printer.svg"),
    (("实验耗材", "白大褂", "防护镜", "面包板", "实验"), "/assets/lab.svg"),
    (("文具用品", "学习办公", "文具", "文件夹", "资料盒", "便利贴"), "/assets/stationery.svg"),
    (("宿舍电器", "电煮锅", "电饭煲", "水壶", "循环扇", "小锅"), "/assets/kettle.svg"),
    (("收纳清洁", "生活用品", "收纳", "压缩袋", "置物架", "清洁"), "/assets/storage.svg"),
    (("床品家纺", "床帘", "枕", "家纺", "床品"), "/assets/bedding.svg"),
    (("厨具餐具", "咖啡", "饭盒", "厨具", "餐具"), "/assets/kitchen.svg"),
    (("家居装饰", "装饰", "台历", "衣帽架", "台灯"), "/assets/decor.svg"),
    (("滑板轮滑", "滑板", "轮滑"), "/assets/skateboard.svg"),
    (("健身器材", "健身", "哑铃", "瑜伽", "拉力带"), "/assets/fitness.svg"),
    (("球类用品", "运动户外", "球拍", "羽毛球", "乒乓", "球类"), "/assets/sports.svg"),
    (("户外露营", "露营", "野餐", "户外"), "/assets/camping.svg"),
    (("乐器文娱", "乐器", "吉他", "尤克里里", "卡林巴"), "/assets/music.svg"),
    (("桌游手办", "桌游", "手办", "uno", "狼人杀"), "/assets/game.svg"),
    (("服装鞋帽", "美妆服饰", "服装", "鞋", "西服"), "/assets/fashion.svg"),
    (("箱包配饰", "箱包", "行李箱", "背包", "电脑包"), "/assets/bag.svg"),
    (("美妆个护", "美妆", "化妆", "卷发", "个护"), "/assets/beauty.svg"),
    (("饰品手表", "饰品", "手表", "项链"), "/assets/watch.svg"),
    (("电脑整机", "电脑配件", "数码", "电脑", "显示器", "硬盘", "键盘", "鼠标"), "/assets/laptop.svg"),
    (("代步", "自行车", "骑行", "车锁", "头盔"), "/assets/bicycle.svg"),
    (("书", "教材", "资料", "考研", "外语", "文学"), "/assets/book.svg"),
]

TOKENS: dict[str, dict[str, int | str]] = {}


def uploads_dir() -> Path:
    return DATA_DIR / "uploads"


class HttpError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(message)


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def hash_password(password: str) -> str:
    return hashlib.sha256(("campus-market:" + password).encode("utf-8")).hexdigest()


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def serialize_db_value(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def row_to_dict(row) -> dict | None:
    if row is None:
        return None
    return {key: serialize_db_value(row[key]) for key in row.keys()}


def rows_to_dicts(rows) -> list[dict]:
    return [row_to_dict(row) for row in rows]


def is_integrity_error(exc: Exception) -> bool:
    return isinstance(exc, sqlite3.IntegrityError) or exc.__class__.__name__ == "IntegrityError"


def create_notification(
    conn,
    user_no: int | None,
    title: str,
    content: str,
    link_type: str | None = None,
    link_no: int | None = None,
) -> None:
    if not user_no:
        return
    conn.execute(
        """
        INSERT INTO Notification(userNo, title, content, linkType, linkNo, createTime)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_no, title, content, link_type, link_no, now_text()),
    )


def require_text(data: dict, field: str, label: str | None = None, max_len: int = 300) -> str:
    value = data.get(field)
    if value is None:
        raise HttpError(400, f"请填写{label or field}")
    value = str(value).strip()
    if not value:
        raise HttpError(400, f"请填写{label or field}")
    if len(value) > max_len:
        raise HttpError(400, f"{label or field}过长")
    return value


def optional_text(data: dict, field: str, max_len: int = 300) -> str | None:
    value = data.get(field)
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    return value[:max_len]


def number_value(data: dict, field: str, label: str, default: float | None = None) -> float:
    value = data.get(field, default)
    if value is None or value == "":
        if default is not None:
            return default
        raise HttpError(400, f"请填写{label}")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise HttpError(400, f"{label}必须是数字")
    if value < 0:
        raise HttpError(400, f"{label}不能为负数")
    return value


def int_value(data: dict, field: str, label: str) -> int:
    value = data.get(field)
    try:
        return int(value)
    except (TypeError, ValueError):
        raise HttpError(400, f"请选择{label}")


def get_query(query: dict[str, list[str]], key: str, default: str = "") -> str:
    values = query.get(key)
    if not values:
        return default
    return values[0].strip()


def require_user_type(value: str | None) -> str:
    user_type = (value or "学生").strip()
    if user_type not in USER_TYPES:
        raise HttpError(400, "用户类型不合法")
    return user_type


def default_image_for_category(conn: sqlite3.Connection, category_no: int) -> str:
    row = conn.execute(
        """
        SELECT c.categoryName, pc.categoryName AS parentName
        FROM Category c
        LEFT JOIN Category pc ON pc.categoryNo = c.parentCategoryNo
        WHERE c.categoryNo = ?
        """,
        (category_no,),
    ).fetchone()
    text = ""
    if row:
        text = f"{row['categoryName']} {row['parentName'] or ''}"
    return default_image_for_category_text(text)


def default_image_for_category_text(text: str | None) -> str:
    normalized = (text or "").lower()
    for keywords, image_url in CATEGORY_IMAGE_RULES:
        if any(keyword.lower() in normalized for keyword in keywords):
            return image_url
    return "/assets/kettle.svg"


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        ensure_sqlite_pre_schema_migrations(conn)
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        ensure_sqlite_migrations(conn)
        seed_db(conn)
        ensure_support_user(conn)


def sqlite_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return bool(row and row[0])


def sqlite_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}


def ensure_sqlite_pre_schema_migrations(conn: sqlite3.Connection) -> None:
    """Patch old local DBs before schema views reference newly added columns."""
    if sqlite_table_exists(conn, "User"):
        user_columns = sqlite_columns(conn, "User")
        user_profile_columns = {
            "gender": "TEXT DEFAULT '保密'",
            "entryYear": "TEXT",
            "avatarUrl": "TEXT",
            "bio": "TEXT",
            "campusCardImageUrl": "TEXT",
            "authSubmitTime": "TEXT",
        }
        for column_name, column_sql in user_profile_columns.items():
            if column_name not in user_columns:
                conn.execute(f"ALTER TABLE User ADD COLUMN {column_name} {column_sql}")

    if sqlite_table_exists(conn, "Item"):
        item_columns = sqlite_columns(conn, "Item")
        if "campusName" not in item_columns:
            conn.execute("ALTER TABLE Item ADD COLUMN campusName TEXT NOT NULL DEFAULT '奉贤校区'")


def ensure_sqlite_migrations(conn: sqlite3.Connection) -> None:
    user_columns = sqlite_columns(conn, "User")
    if "userType" not in user_columns:
        conn.execute("ALTER TABLE User ADD COLUMN userType TEXT NOT NULL DEFAULT '学生'")
        conn.execute("UPDATE User SET userType = '教职工' WHERE studentNo = '24010004'")
        conn.execute("UPDATE User SET userType = '校友' WHERE studentNo = '24010003'")
    user_profile_columns = {
        "gender": "TEXT DEFAULT '保密'",
        "entryYear": "TEXT",
        "avatarUrl": "TEXT",
        "bio": "TEXT",
        "campusCardImageUrl": "TEXT",
        "authSubmitTime": "TEXT",
    }
    for column_name, column_sql in user_profile_columns.items():
        if column_name not in user_columns:
            conn.execute(f"ALTER TABLE User ADD COLUMN {column_name} {column_sql}")

    item_columns = {row["name"] for row in conn.execute("PRAGMA table_info(Item)").fetchall()}
    if "campusName" not in item_columns:
        conn.execute("ALTER TABLE Item ADD COLUMN campusName TEXT NOT NULL DEFAULT '奉贤校区'")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_item_campus ON Item(campusName)")
    apply_user_profile_defaults(conn)
    apply_item_campus_defaults(conn)
    recreate_item_detail_view(conn)
    ensure_sqlite_local_time_triggers(conn)
    migrate_sqlite_utc_defaults_to_local_time(conn)


def ensure_sqlite_local_time_triggers(conn: sqlite3.Connection) -> None:
    """Keep old SQLite tables local-time safe without rebuilding them."""
    for table_name, primary_key, column_name in SQLITE_LOCAL_TIME_TRIGGER_COLUMNS:
        if not sqlite_table_exists(conn, table_name):
            continue
        columns = sqlite_columns(conn, table_name)
        if primary_key not in columns or column_name not in columns:
            continue
        trigger_name = f"trg_{table_name.lower()}_{column_name.lower()}_local_time"
        conn.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS [{trigger_name}]
            AFTER INSERT ON [{table_name}]
            WHEN NEW.[{column_name}] = CURRENT_TIMESTAMP
            BEGIN
                UPDATE [{table_name}]
                   SET [{column_name}] = datetime(NEW.[{column_name}], 'localtime')
                 WHERE [{primary_key}] = NEW.[{primary_key}];
            END
            """
        )


def migrate_sqlite_utc_defaults_to_local_time(conn: sqlite3.Connection) -> None:
    """One-time conversion for timestamps created by SQLite's UTC defaults."""
    current_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current_version >= SQLITE_LOCAL_TIME_MIGRATION_VERSION:
        return

    for table_name, column_name in SQLITE_UTC_HISTORY_COLUMNS:
        if not sqlite_table_exists(conn, table_name):
            continue
        if column_name not in sqlite_columns(conn, table_name):
            continue
        conn.execute(
            f"""
            UPDATE [{table_name}]
               SET [{column_name}] = datetime([{column_name}], 'localtime')
             WHERE [{column_name}] IS NOT NULL
            """
        )
    conn.execute(f"PRAGMA user_version = {SQLITE_LOCAL_TIME_MIGRATION_VERSION}")


def apply_user_profile_defaults(conn) -> None:
    profiles = [
        ("24010001", "男", "2024级", DEFAULT_AVATAR_URL, "喜欢把不用的教材和数码配件流转给真正需要的人。"),
        ("24010002", "女", "2024级", DEFAULT_AVATAR_URL, "搬宿舍清理闲置中，支持校内面交。"),
        ("24010003", "男", "2020级", DEFAULT_AVATAR_URL, "校友回收整理旧资料，偶尔发布一些复习书。"),
        ("24010004", "女", "教职工", DEFAULT_AVATAR_URL, "主要发布课程相关书籍和办公小物。"),
    ]
    for student_no, gender, entry_year, avatar_url, bio in profiles:
        conn.execute(
            """
            UPDATE [User]
               SET gender = CASE WHEN gender IS NULL OR gender = '保密' THEN ? ELSE gender END,
                   entryYear = COALESCE(entryYear, ?),
                   avatarUrl = COALESCE(avatarUrl, ?),
                   bio = COALESCE(bio, ?)
             WHERE studentNo = ?
            """,
            (gender, entry_year, avatar_url, bio, student_no),
        )


def item_campus_defaults() -> dict[str, str]:
    return {
        "数据库系统概论第五版": "徐汇校区",
        "Java 程序设计实验指导": "徐汇校区",
        "英语六级真题与听力资料": "徐汇校区",
        "高等数学同济第七版上下册": "徐汇校区",
        "线性代数辅导讲义": "徐汇校区",
        "计算机408真题解析": "徐汇校区",
        "雅思核心词汇与听力练习册": "徐汇校区",
        "三体全集纪念版": "徐汇校区",
        "ThinkPad X1 Carbon 备用机": "徐汇校区",
        "MacBook Air M1 8G 256G": "徐汇校区",
        "27 英寸 2K 显示器": "奉贤校区",
        "移动固态硬盘 1TB": "徐汇校区",
        "iPhone 13 128G 蓝色": "徐汇校区",
        "小米平板 6 配键盘壳": "奉贤校区",
        "Sony WH-1000XM4 降噪耳机": "徐汇校区",
        "JBL 便携蓝牙音箱": "奉贤校区",
        "佳能微单定焦镜头 50mm": "徐汇校区",
    }


def infer_item_campus(title: str, category_name: str | None = None) -> str:
    defaults = item_campus_defaults()
    if title in defaults:
        return defaults[title]
    text = f"{title} {category_name or ''}"
    if any(keyword in text for keyword in ("自行车", "滑板", "宿舍", "床帘", "收纳", "电饭煲", "循环扇", "咖啡", "哑铃", "羽毛球", "露营")):
        return "奉贤校区"
    return "徐汇校区"


def apply_item_campus_defaults(conn) -> None:
    for title, campus in item_campus_defaults().items():
        conn.execute("UPDATE Item SET campusName = ? WHERE title = ?", (campus, title))
    conn.execute(
        "UPDATE Item SET description = ? WHERE title = ?",
        ("车况稳定，适合通勤，支持私聊约定看车时间。", "校园折叠自行车"),
    )
    conn.execute(
        """
        UPDATE Item
           SET campusName = '奉贤校区'
         WHERE campusName NOT IN ('徐汇校区', '奉贤校区')
            OR campusName IS NULL
        """
    )


def recreate_item_detail_view(conn) -> None:
    conn.execute("DROP VIEW IF EXISTS V_Item_Detail")
    conn.execute(
        """
        CREATE VIEW V_Item_Detail AS
        SELECT
            i.itemNo,
            i.sellerNo,
            u.nickname AS sellerName,
            u.realName AS sellerRealName,
            u.userType AS sellerUserType,
            u.avatarUrl AS sellerAvatarUrl,
            u.bio AS sellerBio,
            u.creditScore,
            u.authStatus AS sellerAuthStatus,
            i.categoryNo,
            c.categoryName,
            c.parentCategoryNo,
            pc.categoryName AS parentCategoryName,
            i.campusName,
            i.title,
            i.description,
            i.originalPrice,
            i.sellPrice,
            i.condition,
            i.imageUrl,
            i.viewCount,
            (SELECT COUNT(*) FROM Favorite f WHERE f.itemNo = i.itemNo) AS favoriteCount,
            i.status,
            i.visible,
            i.publishTime
        FROM Item i
        JOIN [User] u ON u.userNo = i.sellerNo
        JOIN Category c ON c.categoryNo = i.categoryNo
        LEFT JOIN Category pc ON pc.categoryNo = c.parentCategoryNo
        """
    )


def ensure_support_user(conn: sqlite3.Connection) -> None:
    """确保校园客服用户存在，已存在则跳过。"""
    existing = conn.execute(
        "SELECT COUNT(*) FROM [User] WHERE nickname = '校园客服'"
    ).fetchone()[0]
    if existing:
        return
    admin_no = conn.execute("SELECT adminNo FROM Admin LIMIT 1").fetchone()
    conn.execute(
        """
        INSERT INTO [User](studentNo, realName, password, nickname, userType, phone, wechat, authStatus, creditScore, adminNo, registerTime)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("kefu001", "校园客服", hash_password("123456"), "校园客服", "教职工", "", "", "已认证", 100, admin_no[0] if admin_no else None, now_text()),
    )


def seed_db(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM Admin").fetchone()[0] > 0:
        return

    conn.execute(
        "INSERT INTO Admin(username, password, createdTime) VALUES (?, ?, ?)",
        ("admin", hash_password("admin123"), now_text()),
    )
    admin_no = conn.execute("SELECT adminNo FROM Admin WHERE username = 'admin'").fetchone()[0]

    users = [
        ("24010001", "张一凡", "123456", "一凡同学", "学生", "13800010001", "zhang_yf", "已认证", 98),
        ("24010002", "李思雨", "123456", "雨天出清", "学生", "13800010002", "lisi_yu", "已认证", 92),
        ("24010003", "王明泽", "123456", "明泽", "校友", "13800010003", "wmz_03", "待审核", 88),
        ("24010004", "陈可", "123456", "可可买书", "教职工", "13800010004", "chenke", "已认证", 76),
        ("kefu001", "校园客服", "123456", "校园客服", "教职工", "", "", "已认证", 100),
    ]
    for student_no, real_name, password, nickname, user_type, phone, wechat, auth_status, credit in users:
        conn.execute(
            """
            INSERT INTO [User](studentNo, realName, password, nickname, userType, phone, wechat, authStatus, creditScore, adminNo, registerTime)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (student_no, real_name, hash_password(password), nickname, user_type, phone, wechat, auth_status, credit, admin_no, now_text()),
        )

    profiles = [
        ("24010001", "男", "2024级", DEFAULT_AVATAR_URL, "喜欢把不用的教材和数码配件流转给真正需要的人。"),
        ("24010002", "女", "2024级", DEFAULT_AVATAR_URL, "搬宿舍清理闲置中，支持校内面交。"),
        ("24010003", "男", "2020级", DEFAULT_AVATAR_URL, "校友回收整理旧资料，偶尔发布一些复习书。"),
        ("24010004", "女", "教职工", DEFAULT_AVATAR_URL, "主要发布课程相关书籍和办公小物。"),
    ]
    for student_no, gender, entry_year, avatar_url, bio in profiles:
        conn.execute(
            """
            UPDATE [User]
               SET gender = ?, entryYear = ?, avatarUrl = ?, bio = ?
             WHERE studentNo = ?
            """,
            (gender, entry_year, avatar_url, bio, student_no),
        )

    categories = [
        ("书籍教材", None),
        ("专业课教材", "书籍教材"),
        ("考试资料", "书籍教材"),
        ("数码产品", None),
        ("手机平板", "数码产品"),
        ("电脑配件", "数码产品"),
        ("生活用品", None),
        ("代步工具", None),
    ]
    category_ids: dict[str, int] = {}
    for name, parent_name in categories:
        parent_no = category_ids.get(parent_name) if parent_name else None
        conn.execute(
            "INSERT INTO Category(categoryName, parentCategoryNo) VALUES (?, ?)",
            (name, parent_no),
        )
        category_ids[name] = conn.execute(
            """
            SELECT categoryNo
            FROM Category
            WHERE categoryName = ?
              AND ((parentCategoryNo = ?) OR (parentCategoryNo IS NULL AND ? IS NULL))
            """,
            (name, parent_no, parent_no),
        ).fetchone()[0]

    locations = [
        ("具体地点私聊确定", "徐汇校区"),
        ("具体地点私聊确定", "奉贤校区"),
    ]
    for location_name, campus_name in locations:
        conn.execute(
            "INSERT INTO Location(locationName, campusName) VALUES (?, ?)",
            (location_name, campus_name),
        )

    conn.execute(
        """
        INSERT INTO Announcement(adminNo, title, content, publishTime)
        VALUES
        (?, '华东理工大学校园二手交易平台公告', '本平台面向华东理工大学徐汇校区、奉贤校区学生、教职工与校友，支持教材资料、数码设备、宿舍用品、代步工具等校内闲置物品流转。', ?),
        (?, '两校区线下面交安全提醒', '下单时只需先确认徐汇校区或奉贤校区，具体地点由买卖双方通过私聊确认；贵重物品建议选择校内公共区域当面验收。', ?)
        """,
        (admin_no, now_text(), admin_no, now_text()),
    )

    def user_no(student_no: str) -> int:
        return conn.execute("SELECT userNo FROM [User] WHERE studentNo = ?", (student_no,)).fetchone()[0]

    items = [
        (
            "24010001",
            "专业课教材",
            "徐汇校区",
            "数据库系统概论第五版",
            "课堂用书，内页有少量标注，适合数据库原理课程复习。",
            59,
            24,
            "八成新",
            "/assets/book.svg",
        ),
        (
            "24010002",
            "电脑配件",
            "奉贤校区",
            "罗技无线键鼠套装",
            "键盘和鼠标均可正常使用，适合宿舍台式机或笔记本外接。",
            139,
            55,
            "九成新",
            "/assets/laptop.svg",
        ),
        (
            "24010001",
            "代步工具",
            "奉贤校区",
            "校园折叠自行车",
            "车况稳定，适合通勤，支持私聊约定看车时间。",
            499,
            180,
            "七成新",
            "/assets/bicycle.svg",
        ),
        (
            "24010004",
            "生活用品",
            "奉贤校区",
            "宿舍小电煮锅",
            "低功率小锅，已清洗，适合煮面和热汤。",
            89,
            30,
            "八成新",
            "/assets/kettle.svg",
        ),
        (
            "24010002",
            "考试资料",
            "徐汇校区",
            "英语六级真题与听力资料",
            "近三年真题整理，附听力音频链接和作文批注笔记。",
            68,
            22,
            "九成新",
            "/assets/book.svg",
        ),
        (
            "24010004",
            "专业课教材",
            "徐汇校区",
            "Java 程序设计实验指导",
            "课程实验用书，包含 Swing、集合和文件读写例题。",
            42,
            16,
            "八成新",
            "/assets/book.svg",
        ),
        (
            "24010001",
            "手机平板",
            "徐汇校区",
            "iPad 保护壳与电容笔套装",
            "适配 10.2 英寸 iPad，保护壳边角完整，电容笔可正常书写。",
            128,
            48,
            "九成新",
            "/assets/laptop.svg",
        ),
        (
            "24010002",
            "电脑配件",
            "奉贤校区",
            "机械键盘青轴 87 键",
            "键帽已清洁，适合宿舍桌面和编程练习使用。",
            199,
            78,
            "八成新",
            "/assets/laptop.svg",
        ),
        (
            "24010004",
            "生活用品",
            "奉贤校区",
            "护眼台灯可调亮度",
            "三档亮度，USB 供电，适合自习室和宿舍书桌。",
            99,
            35,
            "八成新",
            "/assets/kettle.svg",
        ),
        (
            "24010001",
            "生活用品",
            "奉贤校区",
            "宿舍收纳箱三件套",
            "透明收纳箱，适合衣柜、床下和书桌旁分类整理。",
            75,
            28,
            "九成新",
            "/assets/kettle.svg",
        ),
        (
            "24010002",
            "代步工具",
            "奉贤校区",
            "校园滑板车",
            "折叠款滑板车，刹车正常，适合短距离通勤。",
            269,
            110,
            "七成新",
            "/assets/bicycle.svg",
        ),
        (
            "24010004",
            "手机平板",
            "徐汇校区",
            "蓝牙耳机备用机",
            "续航正常，充电仓有轻微划痕，适合通勤和自习使用。",
            159,
            58,
            "七成新",
            "/assets/laptop.svg",
        ),
    ]
    for seller_student_no, category_name, campus_name, title, description, original, sell, condition, image in items:
        image_url = image
        if image_url in GENERIC_PRODUCT_IMAGES:
            image_url = default_image_for_category_text(f"{title} {category_name}")
        conn.execute(
            """
            INSERT INTO Item(sellerNo, categoryNo, campusName, title, description, originalPrice, sellPrice, condition, imageUrl, publishTime)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_no(seller_student_no),
                category_ids[category_name],
                campus_name,
                title,
                description,
                original,
                sell,
                condition,
                image_url,
                now_text(),
            ),
        )

    conn.execute(
        """
        INSERT INTO Wanted(buyerNo, categoryNo, title, description, expectedPrice, publishTime)
        VALUES (?, ?, '求购 Java 或数据库复习资料', '希望是近两年的资料，最好有重点标注。', 35, ?)
        """,
        (user_no("24010002"), category_ids["考试资料"], now_text()),
    )

    first_item = conn.execute("SELECT itemNo FROM Item WHERE title LIKE '数据库系统概论%'").fetchone()[0]
    conn.execute(
        "INSERT INTO Message(itemNo, userNo, content, msgTime) VALUES (?, ?, ?, ?)",
        (first_item, user_no("24010002"), "请问这本书配套习题册还在吗？", now_text()),
    )
    parent_no = conn.execute("SELECT MAX(messageNo) FROM Message").fetchone()[0]
    conn.execute(
        "INSERT INTO Message(itemNo, userNo, content, msgTime, parentMessageNo) VALUES (?, ?, ?, ?, ?)",
        (first_item, user_no("24010001"), "习题册不在了，只有教材本体。", now_text(), parent_no),
    )
