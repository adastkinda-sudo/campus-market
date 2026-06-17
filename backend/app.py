from __future__ import annotations

import hashlib
import json
import mimetypes
import secrets
import sqlite3
from datetime import date, datetime
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


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


class CampusMarketHandler(BaseHTTPRequestHandler):
    server_version = "CampusMarket/1.0"

    def log_message(self, format, *args):
        return

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()

    def do_GET(self):
        self.handle_request("GET")

    def do_POST(self):
        self.handle_request("POST")

    def do_PUT(self):
        self.handle_request("PUT")

    def do_DELETE(self):
        self.handle_request("DELETE")

    def handle_request(self, method: str):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.handle_api(method, parsed)
        else:
            self.serve_static(parsed.path)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise HttpError(400, "请求体不是合法 JSON")

    def send_json(self, data, status: int = 200):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def serve_static(self, request_path: str):
        path = unquote(request_path)
        if path == "/":
            file_path = FRONTEND_DIR / "index.html"
        else:
            file_path = (FRONTEND_DIR / path.lstrip("/")).resolve()
            if not str(file_path).startswith(str(FRONTEND_DIR.resolve())):
                self.send_error(403)
                return
            if not file_path.exists() or file_path.is_dir():
                file_path = FRONTEND_DIR / "index.html"

        if not file_path.exists():
            self.send_error(404)
            return

        content = file_path.read_bytes()
        content_type, _ = mimetypes.guess_type(str(file_path))
        self.send_response(200)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def handle_api(self, method: str, parsed):
        segments = [unquote(part) for part in parsed.path.strip("/").split("/")[1:]]
        query = parse_qs(parsed.query)
        body = {}
        if method in {"POST", "PUT", "DELETE"}:
            body = self.read_json()

        conn = connect()
        try:
            result = self.route_api(conn, method, segments, query, body)
            if result is None:
                result = {"ok": True}
            self.send_json(result)
        except HttpError as exc:
            self.send_json({"error": exc.message}, exc.status)
        except sqlite3.IntegrityError as exc:
            self.send_json({"error": str(exc)}, 409)
        except Exception as exc:
            if is_integrity_error(exc):
                self.send_json({"error": str(exc)}, 409)
                return
            self.send_json({"error": f"服务器内部错误：{exc}"}, 500)
        finally:
            conn.close()

    def route_api(self, conn: sqlite3.Connection, method: str, segments: list[str], query, body: dict):
        if not segments:
            return {"name": "校园二手物品交易系统", "time": now_text()}

        root = segments[0]
        if root == "auth":
            return self.route_auth(conn, method, segments, body)
        if root == "me" and method == "GET":
            return {"principal": self.current_principal(conn, required=False)}
        if root == "dashboard" and method == "GET":
            return self.get_dashboard(conn)
        if root == "categories":
            return self.route_categories(conn, method, segments, body)
        if root == "locations":
            return self.route_locations(conn, method, segments, body)
        if root == "announcements":
            return self.route_announcements(conn, method, segments, body)
        if root == "items":
            return self.route_items(conn, method, segments, query, body)
        if root == "orders":
            return self.route_orders(conn, method, segments, body)
        if root == "favorites":
            return self.route_favorites(conn, method, segments)
        if root == "notifications":
            return self.route_notifications(conn, method, segments)
        if root == "wanted":
            return self.route_wanted(conn, method, segments, body)
        if root == "reports":
            return self.route_public_reports(conn, method, segments, body)
        if root == "admin":
            return self.route_admin(conn, method, segments, body)
        raise HttpError(404, "接口不存在")

    def current_principal(self, conn: sqlite3.Connection, required: bool = True, roles: tuple[str, ...] | None = None):
        auth = self.headers.get("Authorization", "")
        token = ""
        if auth.startswith("Bearer "):
            token = auth[7:].strip()
        principal = TOKENS.get(token)
        if not principal:
            if required:
                raise HttpError(401, "请先登录")
            return None

        if principal["kind"] == "admin":
            row = conn.execute(
                "SELECT adminNo, username, createdTime FROM Admin WHERE adminNo = ?",
                (principal["id"],),
            ).fetchone()
            if not row:
                raise HttpError(401, "登录状态已失效")
            data = row_to_dict(row)
            data["kind"] = "admin"
        else:
            row = conn.execute(
                """
                SELECT userNo, studentNo, realName, nickname, userType, phone, wechat, authStatus,
                       creditScore, status, registerTime
                FROM [User]
                WHERE userNo = ?
                """,
                (principal["id"],),
            ).fetchone()
            if not row:
                raise HttpError(401, "登录状态已失效")
            data = row_to_dict(row)
            data["kind"] = "user"

        if roles and data["kind"] not in roles:
            raise HttpError(403, "当前账号没有权限执行该操作")
        return data

    def require_admin(self, conn: sqlite3.Connection) -> dict:
        return self.current_principal(conn, roles=("admin",))

    def require_user(self, conn: sqlite3.Connection) -> dict:
        user = self.current_principal(conn, roles=("user",))
        if user["status"] != "正常":
            raise HttpError(403, "该用户已被封禁")
        return user

    def require_verified_user(self, conn: sqlite3.Connection) -> dict:
        user = self.require_user(conn)
        if user["authStatus"] != "已认证":
            raise HttpError(403, "请先完成校园身份认证")
        if user["creditScore"] < 60:
            raise HttpError(403, "信用积分低于 60，暂时不能发布物品或下单")
        return user

    def route_auth(self, conn: sqlite3.Connection, method: str, segments: list[str], body: dict):
        if len(segments) == 2 and segments[1] == "register" and method == "POST":
            student_no = require_text(body, "studentNo", "学号/工号", 40)
            real_name = require_text(body, "realName", "真实姓名", 40)
            password = require_text(body, "password", "密码", 80)
            nickname = require_text(body, "nickname", "昵称", 40)
            user_type = require_user_type(body.get("userType"))
            phone = optional_text(body, "phone", 30)
            wechat = optional_text(body, "wechat", 50)
            with conn:
                conn.execute(
                    """
                    INSERT INTO [User](studentNo, realName, password, nickname, userType, phone, wechat)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (student_no, real_name, hash_password(password), nickname, user_type, phone, wechat),
                )
            return {"message": "注册成功，请登录后提交校园身份认证"}

        if len(segments) == 2 and segments[1] == "login" and method == "POST":
            account = require_text(body, "account", "账号", 80)
            password = require_text(body, "password", "密码", 80)
            password_hash = hash_password(password)

            admin = conn.execute(
                "SELECT adminNo, username FROM Admin WHERE username = ? AND password = ?",
                (account, password_hash),
            ).fetchone()
            if admin:
                token = secrets.token_urlsafe(32)
                TOKENS[token] = {"kind": "admin", "id": admin["adminNo"]}
                principal = row_to_dict(admin)
                principal["kind"] = "admin"
                return {"token": token, "principal": principal}

            user = conn.execute(
                """
                SELECT userNo, studentNo, realName, nickname, userType, phone, wechat,
                       authStatus, creditScore, status, registerTime
                FROM [User]
                WHERE (studentNo = ? OR phone = ? OR nickname = ?) AND password = ?
                """,
                (account, account, account, password_hash),
            ).fetchone()
            if not user:
                raise HttpError(401, "账号或密码错误")
            token = secrets.token_urlsafe(32)
            TOKENS[token] = {"kind": "user", "id": user["userNo"]}
            principal = row_to_dict(user)
            principal["kind"] = "user"
            return {"token": token, "principal": principal}

        if len(segments) == 2 and segments[1] == "logout" and method == "POST":
            auth = self.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                TOKENS.pop(auth[7:].strip(), None)
            return {"message": "已退出登录"}

        if len(segments) == 2 and segments[1] == "submit-auth" and method == "POST":
            user = self.require_user(conn)
            if user["authStatus"] == "已认证":
                return {"message": "已通过认证，无需重复提交"}
            with conn:
                conn.execute("UPDATE [User] SET authStatus = '待审核' WHERE userNo = ?", (user["userNo"],))
            return {"message": "认证申请已提交，等待管理员审核"}

        raise HttpError(404, "认证接口不存在")

    def get_dashboard(self, conn: sqlite3.Connection):
        return {
            "itemCount": conn.execute("SELECT COUNT(*) FROM Item WHERE visible = 1").fetchone()[0],
            "onSaleCount": conn.execute("SELECT COUNT(*) FROM Item WHERE status = '在售' AND visible = 1").fetchone()[0],
            "successOrderCount": conn.execute("SELECT COUNT(*) FROM OrderSheet WHERE orderStatus = '交易成功'").fetchone()[0],
            "userCount": conn.execute("SELECT COUNT(*) FROM [User]").fetchone()[0],
        }

    def route_categories(self, conn: sqlite3.Connection, method: str, segments: list[str], body: dict):
        if method == "GET" and len(segments) == 1:
            rows = conn.execute(
                """
                SELECT c.categoryNo, c.categoryName, c.parentCategoryNo,
                       pc.categoryName AS parentCategoryName,
                       COUNT(i.itemNo) AS itemCount
                FROM Category c
                LEFT JOIN Category pc ON pc.categoryNo = c.parentCategoryNo
                LEFT JOIN Item i ON i.categoryNo = c.categoryNo AND i.visible = 1
                GROUP BY c.categoryNo, c.categoryName, c.parentCategoryNo, pc.categoryName
                ORDER BY COALESCE(c.parentCategoryNo, c.categoryNo),
                         CASE WHEN c.parentCategoryNo IS NOT NULL THEN 1 ELSE 0 END,
                         c.categoryNo
                """
            ).fetchall()
            return {"categories": rows_to_dicts(rows)}

        if method == "POST" and len(segments) == 1:
            self.require_admin(conn)
            name = require_text(body, "categoryName", "分类名称", 40)
            parent_no = body.get("parentCategoryNo")
            parent_no = int(parent_no) if parent_no not in (None, "") else None
            with conn:
                conn.execute(
                    "INSERT INTO Category(categoryName, parentCategoryNo) VALUES (?, ?)",
                    (name, parent_no),
                )
            return {"message": "分类已添加"}

        if len(segments) == 2 and method == "PUT":
            self.require_admin(conn)
            category_no = int(segments[1])
            name = require_text(body, "categoryName", "分类名称", 40)
            parent_no = body.get("parentCategoryNo")
            parent_no = int(parent_no) if parent_no not in (None, "") else None
            if parent_no == category_no:
                raise HttpError(400, "父分类不能选择自己")
            with conn:
                conn.execute(
                    "UPDATE Category SET categoryName = ?, parentCategoryNo = ? WHERE categoryNo = ?",
                    (name, parent_no, category_no),
                )
            return {"message": "分类已更新"}

        if len(segments) == 2 and method == "DELETE":
            self.require_admin(conn)
            category_no = int(segments[1])
            used = conn.execute(
                "SELECT COUNT(*) FROM Item WHERE categoryNo = ?",
                (category_no,),
            ).fetchone()[0]
            child = conn.execute(
                "SELECT COUNT(*) FROM Category WHERE parentCategoryNo = ?",
                (category_no,),
            ).fetchone()[0]
            if used or child:
                raise HttpError(409, "该分类已有子分类或物品，不能删除")
            with conn:
                conn.execute("DELETE FROM Category WHERE categoryNo = ?", (category_no,))
            return {"message": "分类已删除"}

        raise HttpError(404, "分类接口不存在")

    def route_locations(self, conn: sqlite3.Connection, method: str, segments: list[str], body: dict):
        if method == "GET" and len(segments) == 1:
            rows = conn.execute("SELECT * FROM Location ORDER BY campusName, locationNo").fetchall()
            return {"locations": rows_to_dicts(rows)}

        if method == "POST" and len(segments) == 1:
            self.require_admin(conn)
            name = require_text(body, "locationName", "地点名称", 60)
            campus = require_text(body, "campusName", "校区", 60)
            with conn:
                conn.execute("INSERT INTO Location(locationName, campusName) VALUES (?, ?)", (name, campus))
            return {"message": "交易地点已添加"}

        if len(segments) == 2 and method == "PUT":
            self.require_admin(conn)
            location_no = int(segments[1])
            name = require_text(body, "locationName", "地点名称", 60)
            campus = require_text(body, "campusName", "校区", 60)
            with conn:
                conn.execute(
                    "UPDATE Location SET locationName = ?, campusName = ? WHERE locationNo = ?",
                    (name, campus, location_no),
                )
            return {"message": "交易地点已更新"}

        if len(segments) == 2 and method == "DELETE":
            self.require_admin(conn)
            location_no = int(segments[1])
            used = conn.execute("SELECT COUNT(*) FROM OrderSheet WHERE locationNo = ?", (location_no,)).fetchone()[0]
            if used:
                raise HttpError(409, "该地点已有订单使用，不能删除")
            with conn:
                conn.execute("DELETE FROM Location WHERE locationNo = ?", (location_no,))
            return {"message": "交易地点已删除"}

        raise HttpError(404, "地点接口不存在")

    def route_announcements(self, conn: sqlite3.Connection, method: str, segments: list[str], body: dict):
        if method == "GET" and len(segments) == 1:
            rows = conn.execute(
                """
                SELECT a.*, ad.username AS adminName
                FROM Announcement a
                JOIN Admin ad ON ad.adminNo = a.adminNo
                ORDER BY a.publishTime DESC, a.announcementNo DESC
                """
            ).fetchall()
            return {"announcements": rows_to_dicts(rows)}

        if method == "POST" and len(segments) == 1:
            admin = self.require_admin(conn)
            title = require_text(body, "title", "公告标题", 80)
            content = require_text(body, "content", "公告内容", 1000)
            with conn:
                conn.execute(
                    "INSERT INTO Announcement(adminNo, title, content) VALUES (?, ?, ?)",
                    (admin["adminNo"], title, content),
                )
            return {"message": "公告已发布"}

        if method == "DELETE" and len(segments) == 2:
            self.require_admin(conn)
            with conn:
                conn.execute("DELETE FROM Announcement WHERE announcementNo = ?", (int(segments[1]),))
            return {"message": "公告已删除"}

        raise HttpError(404, "公告接口不存在")

    def route_items(self, conn: sqlite3.Connection, method: str, segments: list[str], query, body: dict):
        if method == "GET" and len(segments) == 1:
            return self.list_items(conn, query)
        if method == "POST" and len(segments) == 1:
            return self.create_item(conn, body)
        if len(segments) >= 2:
            item_no = int(segments[1])
            if method == "GET" and len(segments) == 2:
                return self.get_item_detail(conn, item_no)
            if method == "PUT" and len(segments) == 2:
                return self.update_item(conn, item_no, body)
            if method == "DELETE" and len(segments) == 2:
                return self.delete_item(conn, item_no)
            if method == "POST" and len(segments) == 3 and segments[2] == "status":
                return self.change_item_status(conn, item_no, body)
            if method == "POST" and len(segments) == 3 and segments[2] == "messages":
                return self.create_message(conn, item_no, body)
            if method == "POST" and len(segments) == 3 and segments[2] == "orders":
                return self.create_order(conn, item_no, body)
            if len(segments) == 3 and segments[2] == "favorite":
                return self.change_favorite(conn, item_no, method)
        raise HttpError(404, "物品接口不存在")

    def list_items(self, conn: sqlite3.Connection, query):
        keyword = get_query(query, "keyword")
        category = get_query(query, "categoryNo")
        status = get_query(query, "status", "在售")
        sort = get_query(query, "sort", "new")
        clauses = ["visible = 1"]
        params: list = []

        if status != "全部":
            clauses.append("status = ?")
            params.append(status)
        if keyword:
            clauses.append("(title LIKE ? OR description LIKE ? OR sellerName LIKE ?)")
            like = f"%{keyword}%"
            params.extend([like, like, like])
        if category:
            clauses.append("(categoryNo = ? OR parentCategoryNo = ?)")
            params.extend([int(category), int(category)])

        order_sql = {
            "price_asc": "sellPrice ASC, publishTime DESC",
            "price_desc": "sellPrice DESC, publishTime DESC",
            "hot": "viewCount DESC, publishTime DESC",
            "new": "publishTime DESC, itemNo DESC",
        }.get(sort, "publishTime DESC, itemNo DESC")
        rows = conn.execute(
            f"SELECT * FROM V_Item_Detail WHERE {' AND '.join(clauses)} ORDER BY {order_sql}",
            params,
        ).fetchall()
        items = rows_to_dicts(rows)
        principal = self.current_principal(conn, required=False)
        if principal and principal["kind"] == "user" and items:
            item_ids = [item["itemNo"] for item in items]
            placeholders_sql = ", ".join("?" for _ in item_ids)
            favorite_rows = conn.execute(
                f"SELECT itemNo FROM Favorite WHERE userNo = ? AND itemNo IN ({placeholders_sql})",
                [principal["userNo"], *item_ids],
            ).fetchall()
            favorite_ids = {row["itemNo"] for row in favorite_rows}
            for item in items:
                item["isFavorite"] = item["itemNo"] in favorite_ids
        else:
            for item in items:
                item["isFavorite"] = False
        return {"items": items}

    def create_item(self, conn: sqlite3.Connection, body: dict):
        user = self.require_verified_user(conn)
        title = require_text(body, "title", "物品标题", 80)
        description = require_text(body, "description", "物品描述", 1200)
        category_no = int_value(body, "categoryNo", "分类")
        original_price = number_value(body, "originalPrice", "原价")
        sell_price = number_value(body, "sellPrice", "二手价")
        condition = require_text(body, "condition", "新旧程度", 20)
        if condition not in {"全新", "九成新", "八成新", "七成新", "使用痕迹明显"}:
            raise HttpError(400, "新旧程度不合法")
        image_url = optional_text(body, "imageUrl", 300) or default_image_for_category(conn, category_no)
        with conn:
            conn.execute(
                """
                INSERT INTO Item(sellerNo, categoryNo, title, description, originalPrice, sellPrice, condition, imageUrl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user["userNo"], category_no, title, description, original_price, sell_price, condition, image_url),
            )
        return {"message": "物品已发布"}

    def get_item_detail(self, conn: sqlite3.Connection, item_no: int):
        item = conn.execute(
            "SELECT * FROM V_Item_Detail WHERE itemNo = ? AND visible = 1",
            (item_no,),
        ).fetchone()
        if not item:
            raise HttpError(404, "物品不存在")
        with conn:
            conn.execute("UPDATE Item SET viewCount = viewCount + 1 WHERE itemNo = ?", (item_no,))
        item = conn.execute(
            "SELECT * FROM V_Item_Detail WHERE itemNo = ? AND visible = 1",
            (item_no,),
        ).fetchone()
        messages = conn.execute(
            """
            SELECT m.*, u.nickname AS userName, u.creditScore
            FROM Message m
            JOIN [User] u ON u.userNo = m.userNo
            WHERE m.itemNo = ?
            ORDER BY m.msgTime ASC, m.messageNo ASC
            """,
            (item_no,),
        ).fetchall()
        item_dict = row_to_dict(item)
        principal = self.current_principal(conn, required=False)
        if principal and principal["kind"] == "user":
            item_dict["isFavorite"] = (
                conn.execute(
                    "SELECT COUNT(*) FROM Favorite WHERE userNo = ? AND itemNo = ?",
                    (principal["userNo"], item_no),
                ).fetchone()[0]
                > 0
            )
        else:
            item_dict["isFavorite"] = False
        return {"item": item_dict, "messages": rows_to_dicts(messages)}

    def assert_item_owner_or_admin(self, conn: sqlite3.Connection, item_no: int) -> tuple[dict, dict]:
        principal = self.current_principal(conn, roles=("user", "admin"))
        item = conn.execute("SELECT * FROM Item WHERE itemNo = ?", (item_no,)).fetchone()
        if not item:
            raise HttpError(404, "物品不存在")
        item_dict = row_to_dict(item)
        if principal["kind"] == "user" and item_dict["sellerNo"] != principal["userNo"]:
            raise HttpError(403, "只能管理自己发布的物品")
        return principal, item_dict

    def update_item(self, conn: sqlite3.Connection, item_no: int, body: dict):
        _, item = self.assert_item_owner_or_admin(conn, item_no)
        if item["status"] == "已售出":
            raise HttpError(409, "已售出的物品不能修改")
        title = require_text(body, "title", "物品标题", 80)
        description = require_text(body, "description", "物品描述", 1200)
        category_no = int_value(body, "categoryNo", "分类")
        original_price = number_value(body, "originalPrice", "原价")
        sell_price = number_value(body, "sellPrice", "二手价")
        condition = require_text(body, "condition", "新旧程度", 20)
        image_url = optional_text(body, "imageUrl", 300) or default_image_for_category(conn, category_no)
        with conn:
            conn.execute(
                """
                UPDATE Item
                   SET categoryNo = ?, title = ?, description = ?, originalPrice = ?,
                       sellPrice = ?, condition = ?, imageUrl = ?
                 WHERE itemNo = ?
                """,
                (category_no, title, description, original_price, sell_price, condition, image_url, item_no),
            )
        return {"message": "物品信息已更新"}

    def change_item_status(self, conn: sqlite3.Connection, item_no: int, body: dict):
        principal, item = self.assert_item_owner_or_admin(conn, item_no)
        status = require_text(body, "status", "物品状态", 20)
        if status not in {"在售", "已下架"}:
            raise HttpError(400, "只能上架或下架物品")
        active_orders = conn.execute(
            "SELECT COUNT(*) FROM OrderSheet WHERE itemNo = ? AND orderStatus IN ('待卖家确认', '待面交')",
            (item_no,),
        ).fetchone()[0]
        if active_orders and principal["kind"] != "admin":
            raise HttpError(409, "该物品已有进行中的订单，不能自行下架")
        if status == "在售" and item["status"] in {"交易中", "已售出"}:
            raise HttpError(409, "交易中或已售出的物品不能重新上架")
        with conn:
            if principal["kind"] == "admin" and status == "已下架":
                conn.execute(
                    "UPDATE OrderSheet SET orderStatus = '已取消', finishTime = ? WHERE itemNo = ? AND orderStatus IN ('待卖家确认', '待面交')",
                    (now_text(), item_no),
                )
            conn.execute("UPDATE Item SET status = ?, visible = 1 WHERE itemNo = ?", (status, item_no))
        return {"message": "物品状态已更新"}

    def delete_item(self, conn: sqlite3.Connection, item_no: int):
        principal, _ = self.assert_item_owner_or_admin(conn, item_no)
        active_orders = conn.execute(
            "SELECT COUNT(*) FROM OrderSheet WHERE itemNo = ? AND orderStatus IN ('待卖家确认', '待面交')",
            (item_no,),
        ).fetchone()[0]
        if active_orders and principal["kind"] != "admin":
            raise HttpError(409, "该物品已有进行中的订单，不能删除")
        with conn:
            if principal["kind"] == "admin":
                conn.execute(
                    "UPDATE OrderSheet SET orderStatus = '已取消', finishTime = ? WHERE itemNo = ? AND orderStatus IN ('待卖家确认', '待面交')",
                    (now_text(), item_no),
                )
            conn.execute("UPDATE Item SET visible = 0, status = '已下架' WHERE itemNo = ?", (item_no,))
        return {"message": "物品已逻辑删除"}

    def change_favorite(self, conn: sqlite3.Connection, item_no: int, method: str):
        user = self.require_user(conn)
        item = conn.execute(
            "SELECT itemNo, sellerNo, title, visible FROM Item WHERE itemNo = ?",
            (item_no,),
        ).fetchone()
        if not item or item["visible"] != 1:
            raise HttpError(404, "物品不存在")
        if item["sellerNo"] == user["userNo"]:
            raise HttpError(400, "不能收藏自己发布的物品")

        if method == "POST":
            with conn:
                exists = conn.execute(
                    "SELECT COUNT(*) FROM Favorite WHERE userNo = ? AND itemNo = ?",
                    (user["userNo"], item_no),
                ).fetchone()[0]
                if not exists:
                    conn.execute(
                        "INSERT INTO Favorite(userNo, itemNo) VALUES (?, ?)",
                        (user["userNo"], item_no),
                    )
            return {"message": "已加入收藏"}

        if method == "DELETE":
            with conn:
                conn.execute(
                    "DELETE FROM Favorite WHERE userNo = ? AND itemNo = ?",
                    (user["userNo"], item_no),
                )
            return {"message": "已取消收藏"}

        raise HttpError(405, "收藏操作不支持")

    def create_message(self, conn: sqlite3.Connection, item_no: int, body: dict):
        user = self.require_user(conn)
        content = require_text(body, "content", "留言内容", 500)
        parent_no = body.get("parentMessageNo")
        parent_no = int(parent_no) if parent_no not in (None, "") else None
        exists = conn.execute("SELECT COUNT(*) FROM Item WHERE itemNo = ? AND visible = 1", (item_no,)).fetchone()[0]
        if not exists:
            raise HttpError(404, "物品不存在")
        item = conn.execute("SELECT sellerNo, title FROM Item WHERE itemNo = ?", (item_no,)).fetchone()
        parent_user_no = None
        if parent_no:
            parent = conn.execute("SELECT userNo FROM Message WHERE messageNo = ?", (parent_no,)).fetchone()
            parent_user_no = parent["userNo"] if parent else None
        with conn:
            conn.execute(
                "INSERT INTO Message(itemNo, userNo, content, parentMessageNo) VALUES (?, ?, ?, ?)",
                (item_no, user["userNo"], content, parent_no),
            )
            if item and item["sellerNo"] != user["userNo"]:
                create_notification(
                    conn,
                    item["sellerNo"],
                    "你的物品收到新留言",
                    f"{user['nickname']} 在「{item['title']}」下留言：{content[:40]}",
                    "item",
                    item_no,
                )
            if parent_user_no and parent_user_no not in {user["userNo"], item["sellerNo"] if item else None}:
                create_notification(
                    conn,
                    parent_user_no,
                    "你的留言收到回复",
                    f"{user['nickname']} 回复了你在「{item['title']}」下的留言。",
                    "item",
                    item_no,
                )
        return {"message": "留言已发布"}

    def create_order(self, conn: sqlite3.Connection, item_no: int, body: dict):
        user = self.require_verified_user(conn)
        location_no = int_value(body, "locationNo", "交易地点")
        meet_time = require_text(body, "meetTime", "交易时间", 40)
        try:
            conn.execute("BEGIN IMMEDIATE")
            item = conn.execute(
                "SELECT * FROM Item WHERE itemNo = ? AND visible = 1",
                (item_no,),
            ).fetchone()
            if not item:
                raise HttpError(404, "物品不存在")
            if item["sellerNo"] == user["userNo"]:
                raise HttpError(400, "不能购买自己发布的物品")
            if item["status"] != "在售":
                raise HttpError(409, "该物品当前不可购买")
            location_exists = conn.execute("SELECT COUNT(*) FROM Location WHERE locationNo = ?", (location_no,)).fetchone()[0]
            if not location_exists:
                raise HttpError(400, "交易地点不存在")
            conn.execute(
                """
                INSERT INTO OrderSheet(buyerNo, itemNo, locationNo, orderAmount, meetTime)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user["userNo"], item_no, location_no, item["sellPrice"], meet_time),
            )
            order_no = conn.execute(
                "SELECT MAX(orderNo) FROM OrderSheet WHERE buyerNo = ? AND itemNo = ?",
                (user["userNo"], item_no),
            ).fetchone()[0]
            create_notification(
                conn,
                item["sellerNo"],
                "你收到新的订单",
                f"{user['nickname']} 想购买「{item['title']}」，请尽快确认交易。",
                "order",
                order_no,
            )
            conn.commit()
            return {"message": "订单已提交，物品已锁定", "orderNo": order_no}
        except Exception:
            conn.rollback()
            raise

    def route_orders(self, conn: sqlite3.Connection, method: str, segments: list[str], body: dict):
        if len(segments) == 2 and segments[1] == "mine" and method == "GET":
            user = self.require_user(conn)
            rows = conn.execute(
                """
                SELECT * FROM V_Order_Summary
                WHERE buyerNo = ? OR sellerNo = ?
                ORDER BY createTime DESC, orderNo DESC
                """,
                (user["userNo"], user["userNo"]),
            ).fetchall()
            return {"orders": rows_to_dicts(rows)}

        if len(segments) == 3 and segments[2] == "action" and method == "POST":
            return self.change_order_status(conn, int(segments[1]), body)

        if len(segments) == 3 and segments[2] == "reviews" and method == "POST":
            return self.create_review(conn, int(segments[1]), body)

        raise HttpError(404, "订单接口不存在")

    def change_order_status(self, conn: sqlite3.Connection, order_no: int, body: dict):
        user = self.require_user(conn)
        action = require_text(body, "action", "订单操作", 20)
        order = conn.execute("SELECT * FROM V_Order_Summary WHERE orderNo = ?", (order_no,)).fetchone()
        if not order:
            raise HttpError(404, "订单不存在")
        order = row_to_dict(order)
        is_buyer = order["buyerNo"] == user["userNo"]
        is_seller = order["sellerNo"] == user["userNo"]
        if not (is_buyer or is_seller):
            raise HttpError(403, "只能处理与自己相关的订单")

        new_status = None
        if action == "confirm":
            if not is_seller or order["orderStatus"] != "待卖家确认":
                raise HttpError(409, "只有卖家可确认待处理订单")
            new_status = "待面交"
        elif action == "reject":
            if not is_seller or order["orderStatus"] != "待卖家确认":
                raise HttpError(409, "只有卖家可拒绝待处理订单")
            new_status = "已取消"
        elif action == "complete":
            if not is_buyer or order["orderStatus"] != "待面交":
                raise HttpError(409, "只有买家可确认收货")
            new_status = "交易成功"
        elif action == "cancel":
            if order["orderStatus"] not in {"待卖家确认", "待面交"}:
                raise HttpError(409, "该订单当前不能取消")
            new_status = "已取消"
        else:
            raise HttpError(400, "未知订单操作")

        finish_time = now_text() if new_status in {"交易成功", "已取消"} else None
        notify_user_no = None
        notify_title = "订单状态已更新"
        notify_content = f"「{order['itemTitle']}」订单状态更新为：{new_status}。"
        if action == "confirm":
            notify_user_no = order["buyerNo"]
            notify_title = "卖家已确认订单"
            notify_content = f"卖家已确认「{order['itemTitle']}」的交易，请按约定时间地点面交。"
        elif action == "reject":
            notify_user_no = order["buyerNo"]
            notify_title = "卖家已拒绝订单"
            notify_content = f"卖家拒绝了「{order['itemTitle']}」的订单，物品已恢复在售。"
        elif action == "complete":
            notify_user_no = order["sellerNo"]
            notify_title = "买家已确认收货"
            notify_content = f"{user['nickname']} 已确认「{order['itemTitle']}」交易完成。"
        elif action == "cancel":
            notify_user_no = order["sellerNo"] if is_buyer else order["buyerNo"]
            notify_title = "订单已取消"
            notify_content = f"{user['nickname']} 取消了「{order['itemTitle']}」的订单。"
        with conn:
            conn.execute(
                "UPDATE OrderSheet SET orderStatus = ?, finishTime = COALESCE(?, finishTime) WHERE orderNo = ?",
                (new_status, finish_time, order_no),
            )
            create_notification(conn, notify_user_no, notify_title, notify_content, "order", order_no)
        return {"message": "订单状态已更新"}

    def create_review(self, conn: sqlite3.Connection, order_no: int, body: dict):
        user = self.require_user(conn)
        rating = int_value(body, "rating", "评分")
        if rating < 1 or rating > 5:
            raise HttpError(400, "评分必须为 1-5 星")
        content = require_text(body, "content", "评价内容", 500)
        order = conn.execute("SELECT * FROM V_Order_Summary WHERE orderNo = ?", (order_no,)).fetchone()
        if not order:
            raise HttpError(404, "订单不存在")
        order = row_to_dict(order)
        if order["orderStatus"] != "交易成功":
            raise HttpError(409, "只有交易成功后才能评价")
        if user["userNo"] == order["buyerNo"]:
            reviewee_no = order["sellerNo"]
        elif user["userNo"] == order["sellerNo"]:
            reviewee_no = order["buyerNo"]
        else:
            raise HttpError(403, "只能评价自己的订单")
        with conn:
            conn.execute(
                """
                INSERT INTO Review(orderNo, reviewerNo, revieweeNo, rating, content)
                VALUES (?, ?, ?, ?, ?)
                """,
                (order_no, user["userNo"], reviewee_no, rating, content),
            )
            create_notification(
                conn,
                reviewee_no,
                "收到新的交易评价",
                f"{user['nickname']} 给你提交了 {rating} 星评价。",
                "order",
                order_no,
            )
        return {"message": "评价已提交，信用积分已更新"}

    def route_favorites(self, conn: sqlite3.Connection, method: str, segments: list[str]):
        user = self.require_user(conn)
        if method == "GET" and len(segments) == 1:
            rows = conn.execute(
                """
                SELECT d.*, f.favoriteNo, f.createTime AS favoriteTime
                FROM Favorite f
                JOIN V_Item_Detail d ON d.itemNo = f.itemNo
                WHERE f.userNo = ? AND d.visible = 1
                ORDER BY f.createTime DESC, f.favoriteNo DESC
                """,
                (user["userNo"],),
            ).fetchall()
            items = rows_to_dicts(rows)
            for item in items:
                item["isFavorite"] = True
            return {"items": items}
        raise HttpError(404, "收藏接口不存在")

    def route_notifications(self, conn: sqlite3.Connection, method: str, segments: list[str]):
        user = self.require_user(conn)
        if method == "GET" and len(segments) == 1:
            rows = conn.execute(
                """
                SELECT *
                FROM Notification
                WHERE userNo = ?
                ORDER BY isRead ASC, createTime DESC, notificationNo DESC
                """,
                (user["userNo"],),
            ).fetchall()
            unread = conn.execute(
                "SELECT COUNT(*) FROM Notification WHERE userNo = ? AND isRead = 0",
                (user["userNo"],),
            ).fetchone()[0]
            return {"notifications": rows_to_dicts(rows), "unreadCount": unread}

        if method == "POST" and len(segments) == 2 and segments[1] == "read-all":
            with conn:
                conn.execute("UPDATE Notification SET isRead = 1 WHERE userNo = ?", (user["userNo"],))
            return {"message": "通知已全部标记为已读"}

        if method == "POST" and len(segments) == 3 and segments[2] == "read":
            notification_no = int(segments[1])
            with conn:
                conn.execute(
                    "UPDATE Notification SET isRead = 1 WHERE notificationNo = ? AND userNo = ?",
                    (notification_no, user["userNo"]),
                )
            return {"message": "通知已读"}

        raise HttpError(404, "通知接口不存在")

    def route_wanted(self, conn: sqlite3.Connection, method: str, segments: list[str], body: dict):
        if method == "GET" and len(segments) == 1:
            rows = conn.execute(
                """
                SELECT w.*, u.nickname AS buyerName, c.categoryName
                FROM Wanted w
                JOIN [User] u ON u.userNo = w.buyerNo
                LEFT JOIN Category c ON c.categoryNo = w.categoryNo
                WHERE w.status = '有效'
                ORDER BY w.publishTime DESC, w.wantedNo DESC
                """
            ).fetchall()
            return {"wanted": rows_to_dicts(rows)}

        if method == "POST" and len(segments) == 1:
            user = self.require_verified_user(conn)
            title = require_text(body, "title", "求购标题", 80)
            description = require_text(body, "description", "求购描述", 1000)
            category_no = body.get("categoryNo")
            category_no = int(category_no) if category_no not in (None, "") else None
            expected_price = body.get("expectedPrice")
            expected_price = float(expected_price) if expected_price not in (None, "") else None
            with conn:
                conn.execute(
                    """
                    INSERT INTO Wanted(buyerNo, categoryNo, title, description, expectedPrice)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user["userNo"], category_no, title, description, expected_price),
                )
            return {"message": "求购信息已发布"}

        if method == "PUT" and len(segments) == 2:
            principal = self.current_principal(conn, roles=("user", "admin"))
            wanted_no = int(segments[1])
            wanted = conn.execute("SELECT * FROM Wanted WHERE wantedNo = ?", (wanted_no,)).fetchone()
            if not wanted:
                raise HttpError(404, "求购信息不存在")
            if principal["kind"] == "user" and wanted["buyerNo"] != principal["userNo"]:
                raise HttpError(403, "只能关闭自己的求购信息")
            status = require_text(body, "status", "状态", 20)
            if status not in {"有效", "已关闭"}:
                raise HttpError(400, "求购状态不合法")
            with conn:
                conn.execute("UPDATE Wanted SET status = ? WHERE wantedNo = ?", (status, wanted_no))
            return {"message": "求购状态已更新"}

        raise HttpError(404, "求购接口不存在")

    def route_public_reports(self, conn: sqlite3.Connection, method: str, segments: list[str], body: dict):
        if method == "POST" and len(segments) == 1:
            user = self.require_user(conn)
            target_type = require_text(body, "targetType", "举报对象", 20)
            if target_type not in {"物品", "用户"}:
                raise HttpError(400, "举报对象类型不合法")
            target_no = int_value(body, "targetNo", "举报对象")
            reason = require_text(body, "reason", "举报原因", 800)
            if target_type == "物品":
                exists = conn.execute("SELECT COUNT(*) FROM Item WHERE itemNo = ?", (target_no,)).fetchone()[0]
            else:
                exists = conn.execute("SELECT COUNT(*) FROM [User] WHERE userNo = ?", (target_no,)).fetchone()[0]
            if not exists:
                raise HttpError(404, "举报对象不存在")
            with conn:
                conn.execute(
                    "INSERT INTO Report(reporterNo, targetType, targetNo, reason) VALUES (?, ?, ?, ?)",
                    (user["userNo"], target_type, target_no, reason),
                )
            return {"message": "举报已提交，等待管理员处理"}
        raise HttpError(404, "举报接口不存在")

    def route_admin(self, conn: sqlite3.Connection, method: str, segments: list[str], body: dict):
        admin = self.require_admin(conn)
        if len(segments) == 2 and segments[1] == "auth-requests" and method == "GET":
            rows = conn.execute(
                """
                SELECT userNo, studentNo, realName, nickname, userType, phone, wechat, authStatus, creditScore, registerTime
                FROM [User]
                WHERE authStatus = '待审核'
                ORDER BY registerTime ASC
                """
            ).fetchall()
            return {"requests": rows_to_dicts(rows)}

        if len(segments) == 4 and segments[1] == "users" and segments[3] == "auth" and method == "POST":
            user_no = int(segments[2])
            auth_status = require_text(body, "authStatus", "认证结果", 20)
            if auth_status not in {"已认证", "认证驳回"}:
                raise HttpError(400, "认证结果不合法")
            with conn:
                conn.execute(
                    "UPDATE [User] SET authStatus = ?, adminNo = ? WHERE userNo = ?",
                    (auth_status, admin["adminNo"], user_no),
                )
                create_notification(
                    conn,
                    user_no,
                    "校园身份认证结果",
                    f"你的校园身份认证已更新为：{auth_status}。",
                    "account",
                    user_no,
                )
            return {"message": "认证状态已更新"}

        if len(segments) == 4 and segments[1] == "users" and segments[3] == "status" and method == "POST":
            user_no = int(segments[2])
            status = require_text(body, "status", "用户状态", 20)
            if status not in {"正常", "封禁"}:
                raise HttpError(400, "用户状态不合法")
            with conn:
                conn.execute("UPDATE [User] SET status = ? WHERE userNo = ?", (status, user_no))
            return {"message": "用户状态已更新"}

        if len(segments) == 2 and segments[1] == "users" and method == "GET":
            rows = conn.execute(
                """
                SELECT userNo, studentNo, realName, nickname, userType, phone, wechat,
                       authStatus, creditScore, status, registerTime
                FROM [User]
                ORDER BY registerTime DESC
                """
            ).fetchall()
            return {"users": rows_to_dicts(rows)}

        if len(segments) == 2 and segments[1] == "reports" and method == "GET":
            rows = conn.execute(
                """
                SELECT
                    r.*,
                    reporter.nickname AS reporterName,
                    CASE
                        WHEN r.targetType = '物品' THEN (SELECT title FROM Item WHERE itemNo = r.targetNo)
                        ELSE (SELECT nickname FROM [User] WHERE userNo = r.targetNo)
                    END AS targetName
                FROM Report r
                JOIN [User] reporter ON reporter.userNo = r.reporterNo
                ORDER BY r.reportStatus ASC, r.createTime DESC, r.reportNo DESC
                """
            ).fetchall()
            return {"reports": rows_to_dicts(rows)}

        if len(segments) == 4 and segments[1] == "reports" and segments[3] == "handle" and method == "POST":
            return self.handle_report(conn, int(segments[2]), body, admin["adminNo"])

        if len(segments) == 2 and segments[1] == "risky-users" and method == "GET":
            rows = conn.execute("SELECT * FROM V_Risky_User ORDER BY creditScore ASC, reportCount DESC").fetchall()
            return {"users": rows_to_dicts(rows)}

        if len(segments) == 2 and segments[1] == "stats" and method == "GET":
            order_rows = conn.execute(
                "SELECT orderStatus, COUNT(*) AS statusCount FROM OrderSheet GROUP BY orderStatus"
            ).fetchall()
            item_rows = conn.execute(
                "SELECT status, COUNT(*) AS statusCount FROM Item WHERE visible = 1 GROUP BY status"
            ).fetchall()
            top_category_rows = conn.execute(
                """
                SELECT c.categoryName, COUNT(i.itemNo) AS itemCount
                FROM Category c
                LEFT JOIN Item i ON i.categoryNo = c.categoryNo AND i.visible = 1
                GROUP BY c.categoryNo, c.categoryName
                ORDER BY itemCount DESC, c.categoryNo ASC
                """
            ).fetchall()
            user_type_rows = conn.execute(
                "SELECT userType, COUNT(*) AS userCount FROM [User] GROUP BY userType ORDER BY userCount DESC"
            ).fetchall()
            return {
                "totalFavorites": conn.execute("SELECT COUNT(*) FROM Favorite").fetchone()[0],
                "unreadReports": conn.execute("SELECT COUNT(*) FROM Report WHERE reportStatus = '未处理'").fetchone()[0],
                "orders": rows_to_dicts(order_rows),
                "items": rows_to_dicts(item_rows),
                "topCategories": rows_to_dicts(top_category_rows),
                "userTypes": rows_to_dicts(user_type_rows),
            }

        raise HttpError(404, "后台接口不存在")

    def handle_report(self, conn: sqlite3.Connection, report_no: int, body: dict, admin_no: int):
        result = require_text(body, "handleResult", "处理结果", 800)
        action = optional_text(body, "action", 40) or "仅记录"
        report = conn.execute("SELECT * FROM Report WHERE reportNo = ?", (report_no,)).fetchone()
        if not report:
            raise HttpError(404, "举报不存在")
        if report["reportStatus"] == "已处理":
            raise HttpError(409, "该举报已处理")

        with conn:
            if action == "强制下架" and report["targetType"] == "物品":
                conn.execute(
                    "UPDATE OrderSheet SET orderStatus = '已取消', finishTime = ? WHERE itemNo = ? AND orderStatus IN ('待卖家确认', '待面交')",
                    (now_text(), report["targetNo"]),
                )
                conn.execute("UPDATE Item SET status = '已下架' WHERE itemNo = ?", (report["targetNo"],))
            elif action == "封禁用户" and report["targetType"] == "用户":
                conn.execute(
                    "UPDATE [User] SET status = '封禁', creditScore = CASE WHEN creditScore - 20 < 0 THEN 0 ELSE creditScore - 20 END WHERE userNo = ?",
                    (report["targetNo"],),
                )
            elif action == "扣信用分":
                target_user_no = None
                if report["targetType"] == "用户":
                    target_user_no = report["targetNo"]
                else:
                    row = conn.execute("SELECT sellerNo FROM Item WHERE itemNo = ?", (report["targetNo"],)).fetchone()
                    target_user_no = row["sellerNo"] if row else None
                if target_user_no:
                    conn.execute(
                        "UPDATE [User] SET creditScore = CASE WHEN creditScore - 10 < 0 THEN 0 ELSE creditScore - 10 END WHERE userNo = ?",
                        (target_user_no,),
                    )

            conn.execute(
                """
                UPDATE Report
                   SET reportStatus = '已处理',
                       handleResult = ?,
                       handleAdminNo = ?,
                       handleTime = ?
                 WHERE reportNo = ?
                """,
                (f"{action}：{result}", admin_no, now_text(), report_no),
            )
            create_notification(
                conn,
                report["reporterNo"],
                "举报处理完成",
                f"你提交的举报已处理，处理结果：{action}。",
                "report",
                report_no,
            )
        return {"message": "举报已处理"}


def main():
    init_db()
    host = "127.0.0.1"
    port = 8000
    server = ThreadingHTTPServer((host, port), CampusMarketHandler)
    print(f"校园二手物品交易系统已启动：http://{host}:{port}")
    print("演示账号：管理员 admin/admin123；用户 24010001/123456、24010002/123456")
    server.serve_forever()


if __name__ == "__main__":
    main()
