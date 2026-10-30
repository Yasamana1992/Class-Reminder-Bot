import sqlite3
import os
from dotenv import load_dotenv

DB_NAME = "class_reminder.db"

def create_connection():
    connection = sqlite3.connect(DB_NAME)
    return connection

def create_admins_table():
    connection = create_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            role TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()

def add_admin(user_id: int, role: str = "admin") -> bool:
    if role not in ("owner", "admin"):
        raise ValueError("Invalid admin role")
    
    connection = create_connection()

    cursor = connection.execute(
        "INSERT OR IGNORE INTO admins(user_id, role) VALUES (?, ?)",
        (user_id, role)
    )    

    connection.commit()
    added = cursor.rowcount == 1
    connection.close()

    return added

def get_admin_role(user_id: int):
    connection = create_connection()

    result = connection.execute(
        "SELECT role FROM admins WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    connection.close()

    if result is None:
        return None

    return result[0]

def remove_admin(user_id: int) -> bool:
    connection = create_connection()

    cursor = connection.execute(
        "DELETE FROM admins WHERE user_id = ? AND role = ?",
        (user_id, "admin")
    )

    connection.commit()
    removed = cursor.rowcount == 1
    connection.close()

    return removed

def create_students_table():
    connection = create_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            phone TEXT,
            telegram_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()

def add_student(full_name: str, phone: str | None = None, telegram_id: int | None = None) -> bool:
    if not full_name.strip():
        raise ValueError("Invalid name")

    full_name = full_name.strip()
    
    connection = create_connection()

    cursor = connection.execute(
        "INSERT OR IGNORE INTO students(full_name, phone, telegram_id) VALUES (?, ?, ?)",
        (full_name, phone, telegram_id)
    )    

    connection.commit()
    added = cursor.rowcount == 1
    connection.close()

    return added


def get_students():
    connection = create_connection()

    cursor = connection.execute("SELECT * FROM students")
    students = cursor.fetchall()

    connection.close()

    return students

def delete_student(student_id: int) -> bool:
    connection = create_connection()
    
    cursor = connection.execute(
        "DELETE FROM students WHERE student_id = ?",
        (student_id,)
    )
    
    connection.commit()
    removed = cursor.rowcount == 1
    connection.close()
    
    return removed


if __name__ == "__main__":
    load_dotenv()

    owner_id = int(os.getenv("OWNER_ID", "0"))

    if owner_id == 0:
        raise RuntimeError("OWNER_ID is missing from .env")

    create_admins_table()
    add_admin(owner_id, "owner")

    create_students_table()
