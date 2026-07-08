from __future__ import annotations

import hashlib
import sqlite3
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "campus_market.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
USER_TYPES = {"学生", "教职工", "校友"}

TOKENS: dict[str, dict[str, int | str]] = {}


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
        INSERT INTO Notification(userNo, title, content, linkType, linkNo)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_no, title, content, link_type, link_no),
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
    if "书" in text or "教材" in text:
        return "/assets/book.svg"
    if "数码" in text or "电脑" in text or "手机" in text:
        return "/assets/laptop.svg"
    if "代步" in text or "车" in text:
        return "/assets/bicycle.svg"
    return "/assets/kettle.svg"


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        ensure_sqlite_migrations(conn)
        seed_db(conn)


def ensure_sqlite_migrations(conn: sqlite3.Connection) -> None:
    user_columns = {row["name"] for row in conn.execute("PRAGMA table_info(User)").fetchall()}
    if "userType" not in user_columns:
        conn.execute("ALTER TABLE User ADD COLUMN userType TEXT NOT NULL DEFAULT '学生'")
        conn.execute("UPDATE User SET userType = '教职工' WHERE studentNo = '24010004'")
        conn.execute("UPDATE User SET userType = '校友' WHERE studentNo = '24010003'")


def seed_db(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM Admin").fetchone()[0] > 0:
        return

    conn.execute(
        "INSERT INTO Admin(username, password) VALUES (?, ?)",
        ("admin", hash_password("admin123")),
    )
    admin_no = conn.execute("SELECT adminNo FROM Admin WHERE username = 'admin'").fetchone()[0]

    users = [
        ("24010001", "张一凡", "123456", "一凡同学", "学生", "13800010001", "zhang_yf", "已认证", 98),
        ("24010002", "李思雨", "123456", "雨天出清", "学生", "13800010002", "lisi_yu", "已认证", 92),
        ("24010003", "王明泽", "123456", "明泽", "校友", "13800010003", "wmz_03", "待审核", 88),
        ("24010004", "陈可", "123456", "可可买书", "教职工", "13800010004", "chenke", "已认证", 76),
    ]
    for student_no, real_name, password, nickname, user_type, phone, wechat, auth_status, credit in users:
        conn.execute(
            """
            INSERT INTO [User](studentNo, realName, password, nickname, userType, phone, wechat, authStatus, creditScore, adminNo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (student_no, real_name, hash_password(password), nickname, user_type, phone, wechat, auth_status, credit, admin_no),
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
        ("南门", "主校区"),
        ("一食堂门口", "主校区"),
        ("图书馆北门", "主校区"),
        ("信息楼大厅", "主校区"),
        ("东区宿舍楼下", "东校区"),
    ]
    for location_name, campus_name in locations:
        conn.execute(
            "INSERT INTO Location(locationName, campusName) VALUES (?, ?)",
            (location_name, campus_name),
        )

    conn.execute(
        """
        INSERT INTO Announcement(adminNo, title, content)
        VALUES
        (?, '毕业季二手交易提醒', '请优先选择校内公共区域面交，贵重物品当面确认成色和配件。'),
        (?, '平台试运行公告', '本系统用于数据库原理实验演示，已支持浏览、下单、留言、评价、举报和后台审核。')
        """,
        (admin_no, admin_no),
    )

    def user_no(student_no: str) -> int:
        return conn.execute("SELECT userNo FROM [User] WHERE studentNo = ?", (student_no,)).fetchone()[0]

    items = [
        (
            "24010001",
            "专业课教材",
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
            "校园折叠自行车",
            "车况稳定，适合通勤，支持信息楼附近看车。",
            499,
            180,
            "七成新",
            "/assets/bicycle.svg",
        ),
        (
            "24010004",
            "生活用品",
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
            "蓝牙耳机备用机",
            "续航正常，充电仓有轻微划痕，适合通勤和自习使用。",
            159,
            58,
            "七成新",
            "/assets/laptop.svg",
        ),
    ]
    for seller_student_no, category_name, title, description, original, sell, condition, image in items:
        conn.execute(
            """
            INSERT INTO Item(sellerNo, categoryNo, title, description, originalPrice, sellPrice, condition, imageUrl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_no(seller_student_no),
                category_ids[category_name],
                title,
                description,
                original,
                sell,
                condition,
                image,
            ),
        )

    conn.execute(
        """
        INSERT INTO Wanted(buyerNo, categoryNo, title, description, expectedPrice)
        VALUES (?, ?, '求购 Java 或数据库复习资料', '希望是近两年的资料，最好有重点标注。', 35)
        """,
        (user_no("24010002"), category_ids["考试资料"]),
    )

    first_item = conn.execute("SELECT itemNo FROM Item WHERE title LIKE '数据库系统概论%'").fetchone()[0]
    conn.execute(
        "INSERT INTO Message(itemNo, userNo, content) VALUES (?, ?, ?)",
        (first_item, user_no("24010002"), "请问这本书配套习题册还在吗？"),
    )
    parent_no = conn.execute("SELECT MAX(messageNo) FROM Message").fetchone()[0]
    conn.execute(
        "INSERT INTO Message(itemNo, userNo, content, parentMessageNo) VALUES (?, ?, ?, ?)",
        (first_item, user_no("24010001"), "习题册不在了，只有教材本体。", parent_no),
    )
