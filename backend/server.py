from __future__ import annotations

import base64
import json
import mimetypes
import re
import secrets
import sqlite3
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from core import (
    FRONTEND_DIST_DIR,
    FRONTEND_DIR,
    TOKENS,
    HttpError,
    connect,
    create_notification,
    default_image_for_category,
    get_query,
    hash_password,
    init_db,
    int_value,
    is_integrity_error,
    now_text,
    number_value,
    optional_text,
    require_text,
    require_user_type,
    row_to_dict,
    rows_to_dicts,
    uploads_dir,
)


ECUST_CAMPUSES = ("徐汇校区", "奉贤校区")
IMAGE_DATA_RE = re.compile(r"^data:(image/(?:png|jpe?g|webp|gif));base64,(.+)$", re.IGNORECASE | re.DOTALL)
IMAGE_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
UPLOAD_PURPOSES = {"avatar", "campus-card", "item", "feedback"}
MAX_UPLOAD_BYTES = 3 * 1024 * 1024


def require_ecust_campus(body: dict) -> str:
    campus = require_text(body, "campusName", "校区", 20)
    if campus not in ECUST_CAMPUSES:
        raise HttpError(400, "校区只能选择徐汇校区或奉贤校区")
    return campus


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
            self.serve_static(parsed.path, parsed.query)

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

    def serve_static(self, request_path: str, query_string: str = ""):
        path = unquote(request_path)
        if path.startswith("/uploads/"):
            if path.startswith("/uploads/campus-card/") and not self.can_view_campus_card(path, query_string):
                self.send_error(403)
                return
            file_path = (uploads_dir() / path.removeprefix("/uploads/")).resolve()
            upload_root = uploads_dir().resolve()
            if not str(file_path).startswith(str(upload_root)):
                self.send_error(403)
                return
            if not file_path.exists() or file_path.is_dir():
                self.send_error(404)
                return
        else:
            if not (FRONTEND_DIST_DIR / "index.html").exists():
                self.serve_missing_frontend_build()
                return
            static_root = FRONTEND_DIST_DIR
            if path == "/":
                file_path = static_root / "index.html"
            else:
                file_path = (static_root / path.lstrip("/")).resolve()
            if not str(file_path).startswith(str(static_root.resolve())):
                self.send_error(403)
                return
            if not file_path.exists() or file_path.is_dir():
                file_path = static_root / "index.html"

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

    def serve_missing_frontend_build(self):
        content = """
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>需要构建前端</title>
    <style>
      body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f8fafc; color: #0f172a; }
      main { max-width: 720px; margin: 12vh auto; padding: 32px; background: white; border: 1px solid #e2e8f0; border-radius: 18px; box-shadow: 0 18px 50px rgba(15, 23, 42, .08); }
      h1 { margin: 0 0 12px; font-size: 28px; }
      p { line-height: 1.7; color: #475569; }
      pre { overflow: auto; padding: 16px; border-radius: 12px; background: #0f172a; color: #e2e8f0; }
    </style>
  </head>
  <body>
    <main>
      <h1>前端还没有构建</h1>
      <p>当前项目已迁移到 Vue 3 + Vite。直接启动 Python 后端前，需要先生成 <code>frontend/dist</code>，否则浏览器不能直接运行 Vue 源码。</p>
      <pre>cd frontend
npm install
npm run build
cd ..
python3 backend/app.py</pre>
      <p>开发联调时也可以同时运行 Python 后端和 <code>npm run dev</code>，然后访问 Vite 显示的地址。</p>
    </main>
  </body>
</html>
""".strip().encode("utf-8")
        self.send_response(503)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def can_view_campus_card(self, upload_path: str, query_string: str) -> bool:
        auth = self.headers.get("Authorization", "")
        token = auth[7:].strip() if auth.startswith("Bearer ") else ""
        if not token:
            token = (parse_qs(query_string).get("token") or [""])[0]
        principal = TOKENS.get(token)
        if not principal:
            return False
        if principal["kind"] == "admin":
            return True
        conn = connect()
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM [User] WHERE userNo = ? AND campusCardImageUrl = ?",
                (principal["id"], upload_path),
            ).fetchone()
            return bool(row and row[0])
        finally:
            conn.close()

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
            return {"name": "华东理工大学校园二手交易系统", "time": now_text()}

        root = segments[0]
        if root == "auth":
            return self.route_auth(conn, method, segments, body)
        if root == "me" and method == "GET":
            return {"principal": self.current_principal(conn, required=False)}
        if root == "me" and method == "PUT":
            return self.update_my_profile(conn, body)
        if root == "uploads":
            return self.route_uploads(conn, method, segments, body)
        if root == "users":
            return self.route_users(conn, method, segments, query)
        if root == "chats":
            return self.route_chats(conn, method, segments, body)
        if root == "contact":
            return self.route_contact(conn, method, segments, body)
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
                SELECT userNo, studentNo, realName, nickname, userType, phone, wechat,
                       gender, entryYear, avatarUrl, bio, campusCardImageUrl, authSubmitTime,
                       authStatus, creditScore, status, registerTime
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

    def public_user_dict(self, user: dict) -> dict:
        return {
            "userNo": user.get("userNo"),
            "nickname": user.get("nickname"),
            "userType": user.get("userType"),
            "authStatus": user.get("authStatus"),
            "creditScore": user.get("creditScore"),
            "status": user.get("status"),
            "gender": user.get("gender") or "保密",
            "entryYear": user.get("entryYear"),
            "avatarUrl": user.get("avatarUrl"),
            "bio": user.get("bio"),
            "registerTime": user.get("registerTime"),
        }

    def route_auth(self, conn: sqlite3.Connection, method: str, segments: list[str], body: dict):
        if len(segments) == 2 and segments[1] == "register" and method == "POST":
            student_no = require_text(body, "studentNo", "学号/工号", 40)
            real_name = require_text(body, "realName", "真实姓名", 40)
            password = require_text(body, "password", "密码", 80)
            nickname = require_text(body, "nickname", "昵称", 40)
            user_type = require_user_type(body.get("userType"))
            phone = optional_text(body, "phone", 30)
            wechat = optional_text(body, "wechat", 50)
            exists = conn.execute(
                "SELECT COUNT(*) FROM [User] WHERE studentNo = ?",
                (student_no,),
            ).fetchone()[0]
            if exists:
                raise HttpError(409, "该学号/工号已注册，请直接登录或换一个账号")
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
                       gender, entryYear, avatarUrl, bio, campusCardImageUrl, authSubmitTime,
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
            campus_card = require_text(body, "campusCardImageUrl", "校园卡照片", 500)
            gender = optional_text(body, "gender", 10) or user.get("gender") or "保密"
            if gender not in {"男", "女", "其他", "保密"}:
                raise HttpError(400, "性别选项不合法")
            entry_year = optional_text(body, "entryYear", 20)
            bio = optional_text(body, "bio", 160)
            avatar_url = optional_text(body, "avatarUrl", 500)
            phone = optional_text(body, "phone", 30)
            wechat = optional_text(body, "wechat", 50)
            with conn:
                conn.execute(
                    """
                    UPDATE [User]
                       SET authStatus = '待审核',
                           gender = ?,
                           entryYear = ?,
                           bio = ?,
                           avatarUrl = COALESCE(?, avatarUrl),
                           phone = COALESCE(?, phone),
                           wechat = COALESCE(?, wechat),
                           campusCardImageUrl = ?,
                           authSubmitTime = ?
                     WHERE userNo = ?
                    """,
                    (gender, entry_year, bio, avatar_url, phone, wechat, campus_card, now_text(), user["userNo"]),
                )
            return {"message": "认证申请已提交，等待管理员审核"}

        if len(segments) == 2 and segments[1] == "reset-password" and method == "POST":
            student_no = require_text(body, "studentNo", "学号/工号", 40)
            real_name = require_text(body, "realName", "真实姓名", 40)
            new_password = require_text(body, "newPassword", "新密码", 80)
            user = conn.execute(
                "SELECT userNo FROM [User] WHERE studentNo = ? AND realName = ?",
                (student_no, real_name),
            ).fetchone()
            if not user:
                raise HttpError(404, "学号与真实姓名不匹配")
            with conn:
                conn.execute(
                    "UPDATE [User] SET password = ? WHERE userNo = ?",
                    (hash_password(new_password), user["userNo"]),
                )
            return {"message": "密码已重置，请使用新密码登录"}

        raise HttpError(404, "认证接口不存在")

    def route_uploads(self, conn: sqlite3.Connection, method: str, segments: list[str], body: dict):
        self.require_user(conn)
        if method != "POST" or len(segments) != 1:
            raise HttpError(404, "上传接口不存在")
        purpose = optional_text(body, "purpose", 30) or "item"
        if purpose not in UPLOAD_PURPOSES:
            raise HttpError(400, "上传用途不合法")
        data_url = require_text(body, "dataUrl", "图片文件", MAX_UPLOAD_BYTES * 2)
        match = IMAGE_DATA_RE.match(data_url)
        if not match:
            raise HttpError(400, "请上传 png、jpg、webp 或 gif 图片")
        mime_type = match.group(1).lower()
        try:
            payload = base64.b64decode(match.group(2), validate=True)
        except ValueError:
            raise HttpError(400, "图片编码不合法")
        if len(payload) > MAX_UPLOAD_BYTES:
            raise HttpError(400, "图片不能超过 3MB")
        target_dir = uploads_dir() / purpose
        target_dir.mkdir(parents=True, exist_ok=True)
        extension = IMAGE_EXTENSIONS.get(mime_type, ".png")
        filename = f"{uuid.uuid4().hex}{extension}"
        target_path = target_dir / filename
        target_path.write_bytes(payload)
        return {"url": f"/uploads/{purpose}/{filename}", "message": "图片已上传"}

    def update_my_profile(self, conn: sqlite3.Connection, body: dict):
        user = self.require_user(conn)
        nickname = require_text(body, "nickname", "昵称", 40)
        gender = optional_text(body, "gender", 10) or "保密"
        if gender not in {"男", "女", "其他", "保密"}:
            raise HttpError(400, "性别选项不合法")
        entry_year = optional_text(body, "entryYear", 20)
        avatar_url = optional_text(body, "avatarUrl", 500)
        bio = optional_text(body, "bio", 160)
        phone = optional_text(body, "phone", 30)
        wechat = optional_text(body, "wechat", 50)
        with conn:
            conn.execute(
                """
                UPDATE [User]
                   SET nickname = ?,
                       gender = ?,
                       entryYear = ?,
                       avatarUrl = ?,
                       bio = ?,
                       phone = ?,
                       wechat = ?
                 WHERE userNo = ?
                """,
                (nickname, gender, entry_year, avatar_url, bio, phone, wechat, user["userNo"]),
            )
        return {"message": "个人资料已更新", "principal": self.current_principal(conn)}

    def route_users(self, conn: sqlite3.Connection, method: str, segments: list[str], query):
        if method != "GET":
            raise HttpError(405, "用户接口不支持该操作")
        if len(segments) == 1:
            keyword = get_query(query, "keyword")
            params: list = []
            where = "status = '正常'"
            if keyword:
                where += " AND (nickname LIKE ? OR realName LIKE ? OR studentNo LIKE ?)"
                like = f"%{keyword}%"
                params.extend([like, like, like])
            rows = conn.execute(
                f"""
                SELECT userNo, nickname, userType, authStatus, creditScore, status,
                       gender, entryYear, avatarUrl, bio, registerTime
                FROM [User]
                WHERE {where}
                ORDER BY authStatus = '已认证' DESC, creditScore DESC, registerTime DESC
                LIMIT 30
                """,
                params,
            ).fetchall()
            return {"users": [self.public_user_dict(row_to_dict(row)) for row in rows]}

        if len(segments) == 2:
            user_no = int(segments[1])
            row = conn.execute(
                """
                SELECT userNo, nickname, userType, authStatus, creditScore, status,
                       gender, entryYear, avatarUrl, bio, registerTime
                FROM [User]
                WHERE userNo = ? AND status = '正常'
                """,
                (user_no,),
            ).fetchone()
            if not row:
                raise HttpError(404, "用户不存在")
            item_rows = conn.execute(
                """
                SELECT *
                FROM V_Item_Detail
                WHERE sellerNo = ?
                  AND visible = 1
                  AND status IN ('在售', '交易中', '已售出')
                ORDER BY publishTime DESC, itemNo DESC
                """,
                (user_no,),
            ).fetchall()
            message_rows = conn.execute(
                """
                SELECT m.*, i.title AS itemTitle, i.itemNo, u.nickname AS userName
                FROM Message m
                JOIN Item i ON i.itemNo = m.itemNo
                JOIN [User] u ON u.userNo = m.userNo
                WHERE i.sellerNo = ?
                  AND i.visible = 1
                ORDER BY m.msgTime DESC, m.messageNo DESC
                LIMIT 30
                """,
                (user_no,),
            ).fetchall()
            return {
                "user": self.public_user_dict(row_to_dict(row)),
                "items": rows_to_dicts(item_rows),
                "messages": rows_to_dicts(message_rows),
            }

        raise HttpError(404, "用户接口不存在")

    def route_chats(self, conn: sqlite3.Connection, method: str, segments: list[str], body: dict):
        user = self.require_verified_user(conn)
        if method == "GET" and len(segments) == 1:
            rows = conn.execute(
                """
                SELECT
                    pc.*,
                    other_user.nickname AS otherName,
                    other_user.userType AS otherUserType,
                    other_user.avatarUrl AS otherAvatarUrl,
                    other_user.authStatus AS otherAuthStatus,
                    i.title AS relatedItemTitle,
                    (
                        SELECT pm.content
                        FROM PrivateMessage pm
                        WHERE pm.conversationNo = pc.conversationNo
                        ORDER BY pm.sendTime DESC, pm.privateMessageNo DESC
                        LIMIT 1
                    ) AS lastContent,
                    (
                        SELECT pm.sendTime
                        FROM PrivateMessage pm
                        WHERE pm.conversationNo = pc.conversationNo
                        ORDER BY pm.sendTime DESC, pm.privateMessageNo DESC
                        LIMIT 1
                    ) AS lastTime,
                    (
                        SELECT COUNT(*)
                        FROM PrivateMessage pm
                        WHERE pm.conversationNo = pc.conversationNo
                          AND pm.senderNo <> ?
                          AND pm.isRead = 0
                    ) AS unreadCount
                FROM PrivateConversation pc
                JOIN [User] other_user
                  ON other_user.userNo = CASE
                    WHEN pc.userOneNo = ? THEN pc.userTwoNo
                    ELSE pc.userOneNo
                  END
                LEFT JOIN Item i ON i.itemNo = pc.relatedItemNo
                WHERE pc.userOneNo = ? OR pc.userTwoNo = ?
                ORDER BY pc.updateTime DESC, pc.conversationNo DESC
                """,
                (user["userNo"], user["userNo"], user["userNo"], user["userNo"]),
            ).fetchall()
            return {"conversations": rows_to_dicts(rows)}

        if method == "POST" and len(segments) == 1:
            target_no = int_value(body, "targetUserNo", "私聊对象")
            if target_no == user["userNo"]:
                raise HttpError(400, "不能和自己私聊")
            target = conn.execute(
                "SELECT userNo, nickname, authStatus, status FROM [User] WHERE userNo = ?",
                (target_no,),
            ).fetchone()
            if not target or target["status"] != "正常":
                raise HttpError(404, "私聊对象不存在")
            if target["authStatus"] != "已认证":
                raise HttpError(403, "只能和已认证用户私聊")
            related_item_no = body.get("relatedItemNo")
            related_item_no = int(related_item_no) if related_item_no not in (None, "") else None
            if related_item_no:
                item = conn.execute("SELECT itemNo FROM Item WHERE itemNo = ? AND visible = 1", (related_item_no,)).fetchone()
                if not item:
                    raise HttpError(404, "关联物品不存在")
            user_one, user_two = sorted((user["userNo"], target_no))
            if related_item_no:
                existing = conn.execute(
                    """
                    SELECT conversationNo
                    FROM PrivateConversation
                    WHERE userOneNo = ? AND userTwoNo = ? AND relatedItemNo = ?
                    """,
                    (user_one, user_two, related_item_no),
                ).fetchone()
            else:
                existing = conn.execute(
                    """
                    SELECT conversationNo
                    FROM PrivateConversation
                    WHERE userOneNo = ? AND userTwoNo = ? AND relatedItemNo IS NULL
                    """,
                    (user_one, user_two),
                ).fetchone()
            if existing:
                return {"conversationNo": existing["conversationNo"], "message": "会话已存在"}
            with conn:
                conn.execute(
                    """
                    INSERT INTO PrivateConversation(userOneNo, userTwoNo, relatedItemNo, updateTime)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_one, user_two, related_item_no, now_text()),
                )
            row = conn.execute(
                """
                SELECT MAX(conversationNo) AS conversationNo
                FROM PrivateConversation
                WHERE userOneNo = ? AND userTwoNo = ?
                """,
                (user_one, user_two),
            ).fetchone()
            return {"conversationNo": row["conversationNo"], "message": "私聊已创建"}

        if len(segments) >= 2:
            conversation_no = int(segments[1])
            conversation = conn.execute(
                "SELECT * FROM PrivateConversation WHERE conversationNo = ?",
                (conversation_no,),
            ).fetchone()
            if not conversation:
                raise HttpError(404, "会话不存在")
            if user["userNo"] not in {conversation["userOneNo"], conversation["userTwoNo"]}:
                raise HttpError(403, "只能查看自己的私聊")
            other_no = conversation["userTwoNo"] if conversation["userOneNo"] == user["userNo"] else conversation["userOneNo"]

            if method == "GET" and len(segments) == 3 and segments[2] == "messages":
                with conn:
                    conn.execute(
                        "UPDATE PrivateMessage SET isRead = 1 WHERE conversationNo = ? AND senderNo <> ?",
                        (conversation_no, user["userNo"]),
                    )
                other = conn.execute(
                    "SELECT userNo, nickname, userType, avatarUrl, authStatus FROM [User] WHERE userNo = ?",
                    (other_no,),
                ).fetchone()
                rows = conn.execute(
                    """
                    SELECT pm.*, u.nickname AS senderName, u.avatarUrl AS senderAvatarUrl
                    FROM PrivateMessage pm
                    JOIN [User] u ON u.userNo = pm.senderNo
                    WHERE pm.conversationNo = ?
                    ORDER BY pm.sendTime ASC, pm.privateMessageNo ASC
                    """,
                    (conversation_no,),
                ).fetchall()
                return {
                    "conversation": row_to_dict(conversation),
                    "otherUser": row_to_dict(other),
                    "messages": rows_to_dicts(rows),
                }

            if method == "POST" and len(segments) == 3 and segments[2] == "messages":
                content = require_text(body, "content", "私聊内容", 1000)
                with conn:
                    conn.execute(
                        "INSERT INTO PrivateMessage(conversationNo, senderNo, content) VALUES (?, ?, ?)",
                        (conversation_no, user["userNo"], content),
                    )
                    conn.execute(
                        "UPDATE PrivateConversation SET updateTime = ? WHERE conversationNo = ?",
                        (now_text(), conversation_no),
                    )
                    create_notification(
                        conn,
                        other_no,
                        "收到新的私聊消息",
                        f"{user['nickname']}：{content[:40]}",
                        "chat",
                        conversation_no,
                    )
                return {"message": "消息已发送"}

        raise HttpError(404, "私聊接口不存在")

    def route_contact(self, conn: sqlite3.Connection, method: str, segments: list[str], body: dict):
        user = self.require_user(conn)
        if method == "POST" and len(segments) == 1:
            title = require_text(body, "title", "反馈标题", 80)
            content = require_text(body, "content", "反馈内容", 1200)
            with conn:
                conn.execute(
                    "INSERT INTO Feedback(userNo, title, content) VALUES (?, ?, ?)",
                    (user["userNo"], title, content),
                )
            return {"message": "反馈已提交，管理员会尽快回复"}

        if method == "GET" and len(segments) == 2 and segments[1] == "mine":
            rows = conn.execute(
                """
                SELECT f.*, a.username AS adminName
                FROM Feedback f
                LEFT JOIN Admin a ON a.adminNo = f.adminNo
                WHERE f.userNo = ?
                ORDER BY f.createTime DESC, f.feedbackNo DESC
                """,
                (user["userNo"],),
            ).fetchall()
            return {"feedback": rows_to_dicts(rows)}

        raise HttpError(404, "反馈接口不存在")

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
            rows = conn.execute(
                """
                SELECT * FROM Location
                ORDER BY
                    CASE campusName
                        WHEN '徐汇校区' THEN 1
                        WHEN '奉贤校区' THEN 2
                        ELSE 3
                    END,
                    locationNo
                """
            ).fetchall()
            return {"locations": rows_to_dicts(rows)}

        if method == "POST" and len(segments) == 1:
            self.require_admin(conn)
            campus = require_ecust_campus(body)
            name = "具体地点私聊确定"
            with conn:
                conn.execute("INSERT INTO Location(locationName, campusName) VALUES (?, ?)", (name, campus))
            return {"message": "交易校区已添加"}

        if len(segments) == 2 and method == "PUT":
            self.require_admin(conn)
            location_no = int(segments[1])
            campus = require_ecust_campus(body)
            name = "具体地点私聊确定"
            with conn:
                conn.execute(
                    "UPDATE Location SET locationName = ?, campusName = ? WHERE locationNo = ?",
                    (name, campus, location_no),
                )
            return {"message": "交易校区已更新"}

        if len(segments) == 2 and method == "DELETE":
            self.require_admin(conn)
            location_no = int(segments[1])
            used = conn.execute("SELECT COUNT(*) FROM OrderSheet WHERE locationNo = ?", (location_no,)).fetchone()[0]
            if used:
                raise HttpError(409, "该校区已有订单使用，不能删除")
            with conn:
                conn.execute("DELETE FROM Location WHERE locationNo = ?", (location_no,))
            return {"message": "交易校区已删除"}

        raise HttpError(404, "校区接口不存在")

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
        campus = get_query(query, "campusName")
        status = get_query(query, "status", "在售")
        sort = get_query(query, "sort", "new")
        clauses = ["visible = 1"]
        params: list = []

        if status != "全部":
            clauses.append("status = ?")
            params.append(status)
        if keyword:
            clauses.append("(title LIKE ? OR description LIKE ? OR sellerName LIKE ? OR campusName LIKE ? OR categoryName LIKE ? OR parentCategoryName LIKE ?)")
            like = f"%{keyword}%"
            params.extend([like, like, like, like, like, like])
        if category:
            clauses.append("(categoryNo = ? OR parentCategoryNo = ?)")
            params.extend([int(category), int(category)])
        if campus:
            if campus not in ECUST_CAMPUSES:
                raise HttpError(400, "校区只能选择徐汇校区或奉贤校区")
            clauses.append("campusName = ?")
            params.append(campus)

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
        campus = require_ecust_campus(body)
        original_price = number_value(body, "originalPrice", "原价")
        sell_price = number_value(body, "sellPrice", "二手价")
        condition = require_text(body, "condition", "新旧程度", 20)
        if condition not in {"全新", "九成新", "八成新", "七成新", "使用痕迹明显"}:
            raise HttpError(400, "新旧程度不合法")
        image_url = optional_text(body, "imageUrl", 300) or default_image_for_category(conn, category_no)
        with conn:
            conn.execute(
                """
                INSERT INTO Item(sellerNo, categoryNo, campusName, title, description, originalPrice, sellPrice, condition, imageUrl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user["userNo"], category_no, campus, title, description, original_price, sell_price, condition, image_url),
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
        campus = require_ecust_campus(body)
        original_price = number_value(body, "originalPrice", "原价")
        sell_price = number_value(body, "sellPrice", "二手价")
        condition = require_text(body, "condition", "新旧程度", 20)
        image_url = optional_text(body, "imageUrl", 300) or default_image_for_category(conn, category_no)
        with conn:
            conn.execute(
                """
                UPDATE Item
                   SET categoryNo = ?, campusName = ?, title = ?, description = ?, originalPrice = ?,
                       sellPrice = ?, condition = ?, imageUrl = ?
                 WHERE itemNo = ?
                """,
                (category_no, campus, title, description, original_price, sell_price, condition, image_url, item_no),
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
            visible = 0 if status == "已下架" else 1
            conn.execute("UPDATE Item SET status = ?, visible = ? WHERE itemNo = ?", (status, visible, item_no))
        return {"message": "物品状态已更新"}

    def delete_item(self, conn: sqlite3.Connection, item_no: int):
        principal, item = self.assert_item_owner_or_admin(conn, item_no)
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
            if principal["kind"] == "admin":
                create_notification(
                    conn,
                    item["sellerNo"],
                    "物品已被平台下架",
                    f"你发布的「{item['title']}」已由管理员删除并下架。",
                    "item",
                    item_no,
                )
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
                """
                INSERT INTO Message(itemNo, userNo, content, msgTime, parentMessageNo)
                VALUES (?, ?, ?, ?, ?)
                """,
                (item_no, user["userNo"], content, now_text(), parent_no),
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
        location_no = int_value(body, "locationNo", "交易校区")
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
                raise HttpError(400, "交易校区不存在")
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
                SELECT v.*,
                       EXISTS (
                           SELECT 1
                           FROM Review r
                           WHERE r.orderNo = v.orderNo
                             AND r.reviewerNo = ?
                       ) AS reviewedByMe
                FROM V_Order_Summary v
                WHERE v.buyerNo = ? OR v.sellerNo = ?
                ORDER BY createTime DESC, orderNo DESC
                """,
                (user["userNo"], user["userNo"], user["userNo"]),
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
            notify_content = f"卖家已确认「{order['itemTitle']}」的交易，请按约定校区交易，并通过私聊确认具体地点。"
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
                SELECT userNo, studentNo, realName, nickname, userType, phone, wechat,
                       gender, entryYear, avatarUrl, bio, campusCardImageUrl, authSubmitTime,
                       authStatus, creditScore, registerTime
                FROM [User]
                WHERE authStatus = '待审核'
                ORDER BY registerTime ASC
                """
            ).fetchall()
            auth_requests = rows_to_dicts(rows)
            return {"authRequests": auth_requests, "requests": auth_requests}

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
                       gender, entryYear, avatarUrl, bio, campusCardImageUrl, authSubmitTime,
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

        if len(segments) == 2 and segments[1] == "feedback" and method == "GET":
            rows = conn.execute(
                """
                SELECT f.*, u.nickname AS userName, u.userType, u.authStatus
                FROM Feedback f
                JOIN [User] u ON u.userNo = f.userNo
                ORDER BY f.feedbackStatus = '待回复' DESC, f.createTime DESC, f.feedbackNo DESC
                """
            ).fetchall()
            return {"feedback": rows_to_dicts(rows)}

        if len(segments) == 4 and segments[1] == "feedback" and segments[3] == "reply" and method == "POST":
            feedback_no = int(segments[2])
            reply = require_text(body, "reply", "回复内容", 1000)
            feedback = conn.execute("SELECT * FROM Feedback WHERE feedbackNo = ?", (feedback_no,)).fetchone()
            if not feedback:
                raise HttpError(404, "反馈不存在")
            with conn:
                conn.execute(
                    """
                    UPDATE Feedback
                       SET reply = ?,
                           feedbackStatus = '已回复',
                           replyTime = ?,
                           adminNo = ?
                     WHERE feedbackNo = ?
                    """,
                    (reply, now_text(), admin["adminNo"], feedback_no),
                )
                create_notification(
                    conn,
                    feedback["userNo"],
                    "管理员回复了你的反馈",
                    f"你的反馈「{feedback['title']}」已收到回复。",
                    "contact",
                    feedback_no,
                )
            return {"message": "反馈已回复"}

        if len(segments) == 4 and segments[1] == "reports" and segments[3] == "handle" and method == "POST":
            return self.handle_report(conn, int(segments[2]), body, admin["adminNo"])

        if len(segments) == 2 and segments[1] == "risky-users" and method == "GET":
            rows = conn.execute("SELECT * FROM V_Risky_User ORDER BY creditScore ASC, reportCount DESC").fetchall()
            return {"users": rows_to_dicts(rows)}

        if len(segments) == 2 and segments[1] == "stats" and method == "GET":
            return {
                "itemCount": conn.execute("SELECT COUNT(*) FROM Item").fetchone()[0],
                "userCount": conn.execute("SELECT COUNT(*) FROM [User]").fetchone()[0],
                "orderCount": conn.execute("SELECT COUNT(*) FROM OrderSheet").fetchone()[0],
                "unreadReports": conn.execute("SELECT COUNT(*) FROM Report WHERE reportStatus = '未处理'").fetchone()[0],
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
                conn.execute("UPDATE Item SET status = '已下架', visible = 0 WHERE itemNo = ?", (report["targetNo"],))
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
    print(f"华东理工大学校园二手交易系统已启动：http://{host}:{port}")
    print("演示账号：管理员 admin/admin123；用户 24010001/123456、24010002/123456")
    server.serve_forever()


if __name__ == "__main__":
    main()
