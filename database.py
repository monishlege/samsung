import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

import pandas as pd


DB_NAME = os.environ.get(
    "CAMPUS_DB_PATH",
    str(Path(__file__).resolve().parent / "campus.db"),
)
PASSWORD_ITERATIONS = 600_000
PASSWORD_MIN_LENGTH = 12
LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_LOCK_SECONDS = 15 * 60
MAX_LOGIN_FAILURES = 5
VALID_ROLES = {
    "Student",
    "Faculty",
    "Admin",
    "Maintenance Staff",
}
SELF_SIGNUP_ROLES = {"Student", "Faculty"}

def configure_database(path):
    global DB_NAME
    DB_NAME = str(Path(path).expanduser().resolve())


@contextmanager
def _connection():
    db_path = Path(DB_NAME)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path), timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def create_table():
    with _connection() as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (
                    role IN ('Student', 'Faculty', 'Admin', 'Maintenance Staff')
                ),
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                complaint TEXT,
                category TEXT,
                priority TEXT,
                status TEXT DEFAULT 'Pending',
                user_id INTEGER REFERENCES users(id)
            )
        """)
        complaint_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(complaints)")
        }
        if "user_id" not in complaint_columns:
            connection.execute(
                "ALTER TABLE complaints ADD COLUMN user_id "
                "INTEGER REFERENCES users(id)"
            )
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_complaints_user_id
            ON complaints(user_id)
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                username TEXT PRIMARY KEY COLLATE NOCASE,
                failures INTEGER NOT NULL,
                window_started REAL NOT NULL,
                locked_until REAL NOT NULL DEFAULT 0
            )
        """)


def _normalize_username(username):
    return username.strip().lower()


def validate_username(username):
    normalized = _normalize_username(username)
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,29}", normalized):
        raise ValueError(
            "Username must be 3–30 characters using letters, numbers, '.', '_' or '-'."
        )
    return normalized


def hash_password(password):
    if not isinstance(password, str) or not PASSWORD_MIN_LENGTH <= len(password) <= 1024:
        raise ValueError("Password must be between 12 and 1024 characters.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${PASSWORD_ITERATIONS}"
        f"${salt.hex()}${digest.hex()}"
    )


def verify_password(password, encoded_hash):
    if not isinstance(password, str):
        password = ""
    try:
        algorithm, rounds, salt_hex, digest_hex = encoded_hash.split("$")
        iterations = int(rounds)
        if (
            algorithm != "pbkdf2_sha256"
            or not 100_000 <= iterations <= 1_000_000
        ):
            raise ValueError("Unsupported password hash.")
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            iterations,
        )
        return hmac.compare_digest(actual, expected)
    except (AttributeError, TypeError, ValueError):
        return False


def _burn_password_hash(password):
    if not isinstance(password, str):
        password = ""
    hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        secrets.token_bytes(16),
        PASSWORD_ITERATIONS,
    )


def create_user(full_name, username, password, role):
    name = full_name.strip()
    normalized_username = validate_username(username)
    if not name or len(name) > 120:
        raise ValueError("Name must be between 1 and 120 characters.")
    if role not in SELF_SIGNUP_ROLES:
        raise ValueError("Self-registration is limited to Student and Faculty roles.")
    password_hash = hash_password(password)
    try:
        with _connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (full_name, username, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (name, normalized_username, password_hash, role),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError as error:
        raise ValueError("That username is unavailable.") from error


def create_bootstrap_admin(username, password):
    normalized_username = validate_username(username)
    if not isinstance(password, str) or len(password) < 16:
        raise ValueError("The bootstrap admin password must be at least 16 characters.")
    with _connection() as connection:
        admin_count = connection.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'Admin'"
        ).fetchone()[0]
        if admin_count:
            return False
        if connection.execute(
            "SELECT 1 FROM users WHERE username = ?",
            (normalized_username,),
        ).fetchone():
            raise ValueError(
                "The configured admin username already belongs to a non-admin account."
            )
        connection.execute(
            """
            INSERT INTO users (full_name, username, password_hash, role)
            VALUES (?, ?, ?, 'Admin')
            """,
            (
                "Campus Administrator",
                normalized_username,
                hash_password(password),
            ),
        )
    return True


def get_admin_count():
    with _connection() as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'Admin' AND is_active = 1"
        ).fetchone()[0]


def get_user_count():
    with _connection() as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]


def get_user_by_id(user_id):
    with _connection() as connection:
        row = connection.execute(
            """
            SELECT id, full_name, username, role
            FROM users
            WHERE id = ? AND is_active = 1
            """,
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def _record_login_failure(connection, username, now):
    row = connection.execute(
        """
        SELECT failures, window_started, locked_until
        FROM login_attempts
        WHERE username = ?
        """,
        (username,),
    ).fetchone()
    if row is None or now - row["window_started"] >= LOGIN_WINDOW_SECONDS:
        failures = 1
        window_started = now
    else:
        failures = row["failures"] + 1
        window_started = row["window_started"]
    locked_until = now + LOGIN_LOCK_SECONDS if failures >= MAX_LOGIN_FAILURES else 0
    connection.execute(
        """
        INSERT INTO login_attempts (username, failures, window_started, locked_until)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET
            failures = excluded.failures,
            window_started = excluded.window_started,
            locked_until = excluded.locked_until
        """,
        (username, failures, window_started, locked_until),
    )


def authenticate_user(username, password):
    normalized_username = _normalize_username(username)
    now = time.time()
    with _connection() as connection:
        attempt = connection.execute(
            """
            SELECT failures, window_started, locked_until
            FROM login_attempts
            WHERE username = ?
            """,
            (normalized_username,),
        ).fetchone()
        if attempt and attempt["locked_until"] > now:
            _burn_password_hash(password)
            return None

        user = connection.execute(
            """
            SELECT id, full_name, username, password_hash, role
            FROM users
            WHERE username = ? AND is_active = 1
            """,
            (normalized_username,),
        ).fetchone()
        if user:
            valid_password = verify_password(password, user["password_hash"])
        else:
            _burn_password_hash(password)
            valid_password = False
        if user and valid_password:
            connection.execute(
                "DELETE FROM login_attempts WHERE username = ?",
                (normalized_username,),
            )
            return {
                "id": user["id"],
                "full_name": user["full_name"],
                "username": user["username"],
                "role": user["role"],
            }

        _record_login_failure(connection, normalized_username, now)
    return None


def get_users():
    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT id, full_name, username, role, is_active, created_at
            FROM users
            ORDER BY username
            """
        ).fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def update_user_role(actor_id, user_id, role):
    if role not in VALID_ROLES:
        raise ValueError("Invalid account role.")
    with _connection() as connection:
        actor = connection.execute(
            "SELECT role, is_active FROM users WHERE id = ?",
            (actor_id,),
        ).fetchone()
        if not actor or actor["role"] != "Admin" or not actor["is_active"]:
            raise PermissionError("Administrator access is required.")
        target = connection.execute(
            "SELECT role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not target:
            raise ValueError("The selected user no longer exists.")
        if target["role"] == "Admin" and role != "Admin":
            active_admins = connection.execute(
                """
                SELECT COUNT(*) FROM users
                WHERE role = 'Admin' AND is_active = 1
                """
            ).fetchone()[0]
            if active_admins <= 1:
                raise ValueError("The last administrator cannot be demoted.")
        connection.execute(
            "UPDATE users SET role = ? WHERE id = ?",
            (role, user_id),
        )


def add_complaint(user_id, name, complaint, category, priority):
    with _connection() as connection:
        connection.execute(
            """
            INSERT INTO complaints (user_id, name, complaint, category, priority)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, name, complaint, category, priority),
        )


def get_complaints(user_id=None):
    with _connection() as connection:
        if user_id is None:
            query = """
                SELECT id, name, complaint, category, priority, status
                FROM complaints
                ORDER BY id DESC
            """
            return pd.read_sql_query(query, connection)
        query = """
            SELECT id, name, complaint, category, priority, status
            FROM complaints
            WHERE user_id = ?
            ORDER BY id DESC
        """
        return pd.read_sql_query(query, connection, params=(user_id,))
