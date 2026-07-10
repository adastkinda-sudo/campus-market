from __future__ import annotations

import sqlite3
import sys
import tempfile
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


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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


def check_seed_data(conn: sqlite3.Connection) -> None:
    admin = conn.execute(
        "SELECT username, password FROM Admin WHERE username = ?",
        ("admin",),
    ).fetchone()
    assert_true(admin is not None, "admin demo account was not created")
    assert_true(
        admin["password"] == core.hash_password("admin123"),
        "admin demo password hash does not match",
    )
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


def main() -> None:
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

    print("SQLite smoke test passed")


if __name__ == "__main__":
    main()
