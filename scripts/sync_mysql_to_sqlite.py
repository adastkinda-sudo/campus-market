from __future__ import annotations

import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
SQLITE_SCHEMA_PATH = BACKEND_DIR / "schema.sql"
DATA_DIR = ROOT / "data"
SQLITE_DB_PATH = DATA_DIR / "campus_market.db"
TABLES = [
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
]


sys.path.insert(0, str(BACKEND_DIR))
import app_mysql  # noqa: E402


def sqlite_quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def mysql_quote(identifier: str) -> str:
    return app_mysql.quote_identifier(identifier)


def serialize_value(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def sqlite_columns(conn: sqlite3.Connection, table_name: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({sqlite_quote(table_name)})").fetchall()
    return [row["name"] for row in rows]


def mysql_columns(conn, table_name: str) -> list[str]:
    cursor = conn.execute_raw(f"SHOW COLUMNS FROM {mysql_quote(table_name)}")
    return [row[0] for row in cursor.fetchall()]


def fetch_mysql_rows(conn, table_name: str, columns: list[str]):
    column_sql = ", ".join(mysql_quote(column) for column in columns)
    primary_column = columns[0]
    cursor = conn.execute_raw(
        f"SELECT {column_sql} FROM {mysql_quote(table_name)} ORDER BY {mysql_quote(primary_column)}"
    )
    column_names = [description[0] for description in cursor.description]
    return [dict(zip(column_names, row)) for row in cursor.fetchall()]


def copy_table(mysql_conn, sqlite_conn: sqlite3.Connection, table_name: str) -> int:
    sqlite_column_names = sqlite_columns(sqlite_conn, table_name)
    mysql_column_names = set(mysql_columns(mysql_conn, table_name))
    columns = [column for column in sqlite_column_names if column in mysql_column_names]
    if not columns:
        return 0

    rows = fetch_mysql_rows(mysql_conn, table_name, columns)
    if not rows:
        return 0

    column_sql = ", ".join(sqlite_quote(column) for column in columns)
    placeholders = ", ".join(["?"] * len(columns))
    insert_sql = f"INSERT INTO {sqlite_quote(table_name)} ({column_sql}) VALUES ({placeholders})"
    values = [
        tuple(serialize_value(row[column]) for column in columns)
        for row in rows
    ]
    sqlite_conn.executemany(insert_sql, values)
    return len(values)


def build_sqlite_from_mysql(mysql_conn, output_path: Path) -> dict[str, int]:
    if output_path.exists():
        output_path.unlink()
    sqlite_conn = sqlite3.connect(output_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_conn.execute("PRAGMA foreign_keys = OFF")
    sqlite_conn.executescript(SQLITE_SCHEMA_PATH.read_text(encoding="utf-8"))

    trigger_rows = sqlite_conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type = 'trigger' ORDER BY name"
    ).fetchall()
    for row in trigger_rows:
        sqlite_conn.execute(f"DROP TRIGGER IF EXISTS {sqlite_quote(row['name'])}")

    counts: dict[str, int] = {}
    for table_name in TABLES:
        counts[table_name] = copy_table(mysql_conn, sqlite_conn, table_name)

    for row in trigger_rows:
        sqlite_conn.execute(row["sql"])

    sqlite_conn.execute("PRAGMA foreign_keys = ON")
    violations = sqlite_conn.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        sample = [tuple(row) for row in violations[:5]]
        raise RuntimeError(f"SQLite foreign key check failed: {sample}")

    sqlite_conn.commit()
    sqlite_conn.close()
    return counts


def replace_sqlite_db(temp_db_path: Path) -> Path | None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = None
    if SQLITE_DB_PATH.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = Path("/private/tmp") / f"campus_market_sqlite_backup_{stamp}.db"
        shutil.copy2(SQLITE_DB_PATH, backup_path)
    os.replace(temp_db_path, SQLITE_DB_PATH)
    return backup_path


def verify_sqlite_db(counts: dict[str, int]) -> None:
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        for table_name, expected_count in counts.items():
            actual_count = conn.execute(
                f"SELECT COUNT(*) AS n FROM {sqlite_quote(table_name)}"
            ).fetchone()["n"]
            if actual_count != expected_count:
                raise RuntimeError(
                    f"{table_name} count mismatch: expected {expected_count}, got {actual_count}"
                )
        item_count = conn.execute("SELECT COUNT(*) AS n FROM Item").fetchone()["n"]
        view_count = conn.execute("SELECT COUNT(*) AS n FROM V_Item_Detail").fetchone()["n"]
        if item_count != view_count:
            raise RuntimeError(f"V_Item_Detail mismatch: Item={item_count}, View={view_count}")


def main() -> None:
    app_mysql.init_db()
    mysql_conn = app_mysql.connect()
    try:
        with tempfile.TemporaryDirectory(prefix="campus-market-sqlite-sync-") as tmp_dir:
            temp_db_path = Path(tmp_dir) / "campus_market.db"
            counts = build_sqlite_from_mysql(mysql_conn, temp_db_path)
            backup_path = replace_sqlite_db(temp_db_path)
    finally:
        mysql_conn.close()

    verify_sqlite_db(counts)
    print(f"SQLite dataset refreshed from MySQL: {SQLITE_DB_PATH}")
    if backup_path:
        print(f"Previous SQLite backup: {backup_path}")
    for table_name in TABLES:
        print(f"{table_name}: {counts[table_name]}")


if __name__ == "__main__":
    main()
