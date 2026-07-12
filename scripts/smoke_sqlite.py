from __future__ import annotations

import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import core  # noqa: E402
import server  # noqa: E402


EXPECTED_TABLES = {
    "Admin",
    "User",
    "Category",
    "Location",
    "Announcement",
    "Notification",
    "Item",
    "Favorite",
    "Wanted",
    "OrderSheet",
    "Message",
    "PrivateConversation",
    "PrivateMessage",
    "Review",
    "Report",
    "Feedback",
}

EXPECTED_VIEWS = {
    "V_Item_Detail",
    "V_Order_Summary",
    "V_Risky_User",
}

AUTO_TIME_DEFAULTS = {
    "Admin": "createdTime",
    "User": "registerTime",
    "Announcement": "publishTime",
    "Notification": "createTime",
    "Item": "publishTime",
    "Favorite": "createTime",
    "Wanted": "publishTime",
    "OrderSheet": "createTime",
    "Message": "msgTime",
    "PrivateConversation": "createTime",
    "PrivateMessage": "sendTime",
    "Review": "reviewTime",
    "Report": "createTime",
    "Feedback": "createTime",
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_local_current_time(value: str, label: str, before: datetime, after: datetime) -> None:
    parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    assert_true(before.replace(microsecond=0) <= parsed <= after, f"{label} is not local current time")


def fetch_count(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
    return int(conn.execute(sql, params).fetchone()[0])


def check_schema(conn: sqlite3.Connection) -> None:
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    views = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'view'"
        ).fetchall()
    }
    missing_tables = EXPECTED_TABLES - tables
    missing_views = EXPECTED_VIEWS - views
    assert_true(not missing_tables, f"missing tables: {sorted(missing_tables)}")
    assert_true(not missing_views, f"missing views: {sorted(missing_views)}")
    user_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(User)").fetchall()
    }
    expected_user_columns = {
        "gender",
        "entryYear",
        "avatarUrl",
        "bio",
        "campusCardImageUrl",
        "authSubmitTime",
    }
    missing_user_columns = expected_user_columns - user_columns
    assert_true(not missing_user_columns, f"missing user columns: {sorted(missing_user_columns)}")
    for table_name, column_name in AUTO_TIME_DEFAULTS.items():
        columns = {
            row["name"]: row["dflt_value"]
            for row in conn.execute(f"PRAGMA table_info([{table_name}])").fetchall()
        }
        default_value = columns.get(column_name) or ""
        assert_true("localtime" in default_value, f"{table_name}.{column_name} does not default to local time")
    trigger_names = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'").fetchall()
    }
    expected_local_time_triggers = {
        f"trg_{table_name.lower()}_{column_name.lower()}_local_time"
        for table_name, _, column_name in core.SQLITE_LOCAL_TIME_TRIGGER_COLUMNS
    }
    missing_local_time_triggers = expected_local_time_triggers - trigger_names
    assert_true(not missing_local_time_triggers, f"missing local-time triggers: {sorted(missing_local_time_triggers)}")


def check_seed_data(conn: sqlite3.Connection) -> None:
    admin = conn.execute(
        "SELECT username, password, createdTime FROM Admin WHERE username = ?",
        ("admin",),
    ).fetchone()
    assert_true(admin is not None, "admin demo account was not created")
    assert_true(
        admin["password"] == core.hash_password("admin123"),
        "admin demo password hash does not match",
    )
    now = datetime.now()
    assert_local_current_time(admin["createdTime"], "seed admin time", now.replace(microsecond=0), now)
    assert_true(fetch_count(conn, "SELECT COUNT(*) FROM User") >= 4, "demo users missing")
    assert_true(fetch_count(conn, "SELECT COUNT(*) FROM Item") >= 1, "demo items missing")
    assert_true(
        fetch_count(conn, "SELECT COUNT(*) FROM V_Item_Detail") >= 1,
        "item detail view returned no rows",
    )


def check_order_triggers(conn: sqlite3.Connection) -> None:
    item = conn.execute(
        """
        SELECT itemNo, sellerNo, sellPrice
        FROM Item
        WHERE status = '在售' AND visible = 1
        ORDER BY itemNo
        LIMIT 1
        """
    ).fetchone()
    assert_true(item is not None, "no on-sale item available for trigger check")

    buyer = conn.execute(
        """
        SELECT userNo
        FROM User
        WHERE authStatus = '已认证' AND status = '正常' AND userNo <> ?
        ORDER BY userNo
        LIMIT 1
        """,
        (item["sellerNo"],),
    ).fetchone()
    location = conn.execute("SELECT locationNo FROM Location ORDER BY locationNo LIMIT 1").fetchone()
    assert_true(buyer is not None, "no eligible buyer available for trigger check")
    assert_true(location is not None, "no location available for trigger check")

    conn.execute("BEGIN IMMEDIATE")
    conn.execute(
        """
        INSERT INTO OrderSheet(buyerNo, itemNo, locationNo, orderAmount, meetTime)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            buyer["userNo"],
            item["itemNo"],
            location["locationNo"],
            item["sellPrice"],
            "2026-07-08 12:00:00",
        ),
    )
    order_no = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    locked_status = conn.execute(
        "SELECT status FROM Item WHERE itemNo = ?",
        (item["itemNo"],),
    ).fetchone()[0]
    assert_true(locked_status == "交易中", "order insert trigger did not lock item")

    conn.execute(
        "UPDATE OrderSheet SET orderStatus = '已取消' WHERE orderNo = ?",
        (order_no,),
    )
    restored_status = conn.execute(
        "SELECT status FROM Item WHERE itemNo = ?",
        (item["itemNo"],),
    ).fetchone()[0]
    assert_true(restored_status == "在售", "order cancel trigger did not restore item")
    conn.rollback()


def check_admin_auth_requests_contract(conn: sqlite3.Connection) -> None:
    admin = conn.execute("SELECT adminNo FROM Admin ORDER BY adminNo LIMIT 1").fetchone()
    user = conn.execute(
        """
        SELECT userNo
        FROM User
        WHERE authStatus <> '待审核'
        ORDER BY userNo
        LIMIT 1
        """
    ).fetchone()
    assert_true(admin is not None, "admin demo account was not created")
    assert_true(user is not None, "no demo user available for auth request contract check")

    with conn:
        conn.execute(
            """
            UPDATE User
               SET authStatus = '待审核',
                   campusCardImageUrl = '/uploads/campus-card/smoke.png',
                   authSubmitTime = ?
             WHERE userNo = ?
            """,
            (core.now_text(), user["userNo"]),
        )

    token = "smoke-admin-token"
    core.TOKENS[token] = {"kind": "admin", "id": admin["adminNo"]}
    handler = object.__new__(server.CampusMarketHandler)
    handler.headers = {"Authorization": f"Bearer {token}"}
    try:
        result = handler.route_admin(conn, "GET", ["admin", "auth-requests"], {})
    finally:
        core.TOKENS.pop(token, None)

    assert_true("authRequests" in result, "admin auth request response missing authRequests")
    assert_true("requests" in result, "admin auth request response missing compatibility requests")
    assert_true(len(result["authRequests"]) >= 1, "admin auth request response returned no pending users")


def check_admin_stats_contract(conn: sqlite3.Connection) -> None:
    admin = conn.execute("SELECT adminNo FROM Admin ORDER BY adminNo LIMIT 1").fetchone()
    assert_true(admin is not None, "admin demo account was not created")

    token = "smoke-admin-token"
    core.TOKENS[token] = {"kind": "admin", "id": admin["adminNo"]}
    handler = object.__new__(server.CampusMarketHandler)
    handler.headers = {"Authorization": f"Bearer {token}"}
    try:
        result = handler.route_admin(conn, "GET", ["admin", "stats"], {})
    finally:
        core.TOKENS.pop(token, None)

    expected_keys = {"itemCount", "userCount", "orderCount", "unreadReports"}
    missing_keys = expected_keys - result.keys()
    assert_true(not missing_keys, f"admin stats missing keys: {sorted(missing_keys)}")
    assert_true("totalFavorites" not in result, "admin stats still exposes favorite total")
    assert_true("orders" not in result, "admin stats still exposes order status groups")
    assert_true("items" not in result, "admin stats still exposes item status groups")


def check_admin_delete_item_contract(conn: sqlite3.Connection) -> None:
    admin = conn.execute("SELECT adminNo FROM Admin ORDER BY adminNo LIMIT 1").fetchone()
    item = conn.execute(
        """
        SELECT itemNo, sellerNo
        FROM Item
        WHERE visible = 1
        ORDER BY itemNo
        LIMIT 1
        """
    ).fetchone()
    assert_true(admin is not None, "admin demo account was not created")
    assert_true(item is not None, "no visible item available for admin delete check")

    token = "smoke-admin-token"
    core.TOKENS[token] = {"kind": "admin", "id": admin["adminNo"]}
    handler = object.__new__(server.CampusMarketHandler)
    handler.headers = {"Authorization": f"Bearer {token}"}
    before = datetime.now()
    try:
        result = handler.route_items(conn, "DELETE", ["items", str(item["itemNo"])], {}, {})
    finally:
        core.TOKENS.pop(token, None)
    after = datetime.now()

    assert_true(result["message"] == "物品已逻辑删除", "admin item delete returned unexpected message")
    deleted = conn.execute(
        "SELECT visible, status FROM Item WHERE itemNo = ?",
        (item["itemNo"],),
    ).fetchone()
    assert_true(deleted["visible"] == 0, "admin item delete did not hide item")
    assert_true(deleted["status"] == "已下架", "admin item delete did not shelve item")
    notification = conn.execute(
        """
        SELECT createTime
        FROM Notification
        WHERE userNo = ?
          AND linkType = 'item'
          AND linkNo = ?
          AND title = '物品已被平台下架'
        ORDER BY notificationNo DESC
        LIMIT 1
        """,
        (item["sellerNo"], item["itemNo"]),
    ).fetchone()
    assert_true(notification is not None, "admin item delete did not notify seller")
    assert_local_current_time(notification["createTime"], "notification time", before, after)


def check_message_local_time_contract(conn: sqlite3.Connection) -> None:
    item = conn.execute(
        """
        SELECT itemNo
        FROM Item
        WHERE visible = 1
        ORDER BY itemNo
        LIMIT 1
        """
    ).fetchone()
    user = conn.execute("SELECT userNo FROM User ORDER BY userNo LIMIT 1").fetchone()
    assert_true(item is not None, "no visible item available for message check")
    assert_true(user is not None, "no demo user available for message check")

    token = "smoke-user-token"
    core.TOKENS[token] = {"kind": "user", "id": user["userNo"]}
    handler = object.__new__(server.CampusMarketHandler)
    handler.headers = {"Authorization": f"Bearer {token}"}
    before = datetime.now()
    try:
        result = handler.create_message(
            conn,
            item["itemNo"],
            {"content": "smoke local-time message"},
        )
    finally:
        core.TOKENS.pop(token, None)
    after = datetime.now()

    assert_true(result["message"] == "留言已发布", "message creation returned unexpected result")
    row = conn.execute(
        "SELECT msgTime FROM Message WHERE content = ? ORDER BY messageNo DESC LIMIT 1",
        ("smoke local-time message",),
    ).fetchone()
    assert_true(row is not None, "created message was not persisted")
    assert_local_current_time(row["msgTime"], "message time", before, after)


def check_private_message_local_time_contract(conn: sqlite3.Connection) -> None:
    users = conn.execute(
        """
        SELECT userNo
        FROM User
        WHERE authStatus = '已认证' AND status = '正常'
        ORDER BY userNo
        LIMIT 2
        """
    ).fetchall()
    assert_true(len(users) == 2, "not enough verified users for private message check")

    sender_no = users[0]["userNo"]
    target_no = users[1]["userNo"]
    token = "smoke-chat-user-token"
    core.TOKENS[token] = {"kind": "user", "id": sender_no}
    handler = object.__new__(server.CampusMarketHandler)
    handler.headers = {"Authorization": f"Bearer {token}"}
    try:
        conversation = handler.route_chats(
            conn,
            "POST",
            ["chats"],
            {"targetUserNo": target_no},
        )
        before = datetime.now()
        result = handler.route_chats(
            conn,
            "POST",
            ["chats", str(conversation["conversationNo"]), "messages"],
            {"content": "smoke local-time private message"},
        )
        after = datetime.now()
    finally:
        core.TOKENS.pop(token, None)

    assert_true(result["message"] == "消息已发送", "private message creation returned unexpected result")
    row = conn.execute(
        "SELECT sendTime FROM PrivateMessage WHERE content = ? ORDER BY privateMessageNo DESC LIMIT 1",
        ("smoke local-time private message",),
    ).fetchone()
    assert_true(row is not None, "created private message was not persisted")
    assert_local_current_time(row["sendTime"], "private message time", before, after)


def check_legacy_utc_time_migration() -> None:
    legacy_time = "2026-07-12 04:00:00"
    with sqlite3.connect(":memory:") as conn:
        conn.row_factory = sqlite3.Row
        conn.executescript(
            """
            CREATE TABLE Notification (
                notificationNo INTEGER PRIMARY KEY,
                createTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE Message (
                messageNo INTEGER PRIMARY KEY,
                msgTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.execute("INSERT INTO Notification(notificationNo, createTime) VALUES (1, ?)", (legacy_time,))
        conn.execute("INSERT INTO Message(messageNo, msgTime) VALUES (1, ?)", (legacy_time,))
        expected = conn.execute("SELECT datetime(?, 'localtime')", (legacy_time,)).fetchone()[0]

        core.migrate_sqlite_utc_defaults_to_local_time(conn)
        notification_time = conn.execute("SELECT createTime FROM Notification WHERE notificationNo = 1").fetchone()[0]
        message_time = conn.execute("SELECT msgTime FROM Message WHERE messageNo = 1").fetchone()[0]
        assert_true(notification_time == expected, "legacy notification time was not migrated to local time")
        assert_true(message_time == expected, "legacy message time was not migrated to local time")
        assert_true(
            conn.execute("PRAGMA user_version").fetchone()[0] == core.SQLITE_LOCAL_TIME_MIGRATION_VERSION,
            "local-time migration version was not recorded",
        )

        core.migrate_sqlite_utc_defaults_to_local_time(conn)
        unchanged = conn.execute("SELECT createTime FROM Notification WHERE notificationNo = 1").fetchone()[0]
        assert_true(unchanged == expected, "local-time migration was applied more than once")

        core.ensure_sqlite_local_time_triggers(conn)
        before = datetime.now()
        conn.execute("INSERT INTO Notification(notificationNo) VALUES (2)")
        after = datetime.now()
        triggered_time = conn.execute("SELECT createTime FROM Notification WHERE notificationNo = 2").fetchone()[0]
        assert_local_current_time(triggered_time, "legacy-table trigger time", before, after)


def main() -> None:
    check_legacy_utc_time_migration()
    with tempfile.TemporaryDirectory(prefix="campus-market-smoke-") as tmp_dir:
        temp_dir = Path(tmp_dir)
        core.DATA_DIR = temp_dir
        core.DB_PATH = temp_dir / "campus_market.db"
        core.init_db()

        with core.connect() as conn:
            check_schema(conn)
            check_seed_data(conn)
            check_order_triggers(conn)
            check_admin_auth_requests_contract(conn)
            check_admin_stats_contract(conn)
            check_admin_delete_item_contract(conn)
            check_message_local_time_contract(conn)
            check_private_message_local_time_contract(conn)

    print("SQLite smoke test passed")


if __name__ == "__main__":
    main()
