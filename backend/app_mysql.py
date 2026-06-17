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
    for statement in split_mysql_script(script):
        conn.execute_raw(statement)
    conn.commit()


def init_db() -> None:
    ensure_database()
    conn = connect()
    try:
        execute_schema(conn)
        sqlite_app.seed_db(conn)
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


def main():
    init_db()
    host = os.environ.get("CAMPUS_MARKET_HOST", "127.0.0.1")
    port = int(os.environ.get("CAMPUS_MARKET_PORT", "8001"))
    server = sqlite_app.ThreadingHTTPServer((host, port), sqlite_app.CampusMarketHandler)
    print(f"校园二手物品交易系统 MySQL 版已启动：http://{host}:{port}")
    print("演示账号：管理员 admin/admin123；用户 24010001/123456、24010002/123456")
    server.serve_forever()


if __name__ == "__main__":
    main()
