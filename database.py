import sqlite3
import os
from dotenv import load_dotenv
from datetime import datetime

DB_NAME = "class_reminder.db"

def create_connection():
    connection = sqlite3.connect(DB_NAME)
    connection.execute("PRAGMA foreign_keys = ON")
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

def create_classes_table():
    connection = create_connection()
    
    connection.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            class_id INTEGER PRIMARY KEY,
            class_name TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    connection.commit()
    connection.close()

def create_class_schedules_table():
    connection = create_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS class_schedules (
            schedule_id INTEGER PRIMARY KEY,
            class_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,

            FOREIGN KEY (class_id)
            REFERENCES classes(class_id)
            ON DELETE CASCADE,

            CHECK (day_of_week BETWEEN 0 AND 6),
            CHECK (start_time < end_time)
        )
    """)

    connection.commit()
    connection.close()

def create_student_classes_table():
    connection = create_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS student_classes (
            student_id INTEGER NOT NULL,
            class_id INTEGER NOT NULL,
            enrolled_at TEXT DEFAULT CURRENT_TIMESTAMP,

            PRIMARY KEY (student_id, class_id),

            FOREIGN KEY (student_id)
            REFERENCES students(student_id)
            ON DELETE CASCADE,

            FOREIGN KEY (class_id)
            REFERENCES classes(class_id)
            ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()

def add_class(class_name: str, description: str | None = None) -> int:
    if not class_name.strip():
        raise ValueError("Invalid class name")

    class_name = class_name.strip()

    connection = create_connection()

    cursor = connection.execute(
        """
        INSERT INTO classes (class_name, description)
        VALUES (?, ?)
        """,
        (class_name, description)
    )

    connection.commit()
    class_id = cursor.lastrowid
    connection.close()

    return class_id

def get_classes():
    connection = create_connection()

    cursor = connection.execute("""
        SELECT class_id, class_name, description, created_at
        FROM classes
        ORDER BY class_id
    """)

    classes = cursor.fetchall()
    connection.close()

    return classes

def add_class_schedule(
    class_id: int,
    day_of_week: int,
    start_time: str,
    end_time: str
) -> int:

    if not 0 <= day_of_week <= 6:
        raise ValueError("Invalid day of week")

    start = datetime.strptime(start_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")

    if start >= end:
        raise ValueError("End time must be after start time")

    connection = create_connection()

    cursor = connection.execute(
        """
        INSERT INTO class_schedules
        (class_id, day_of_week, start_time, end_time)
        VALUES (?, ?, ?, ?)
        """,
        (class_id, day_of_week, start_time, end_time)
    )

    connection.commit()
    schedule_id = cursor.lastrowid
    connection.close()

    return schedule_id

def get_class_schedules(class_id: int):
    connection = create_connection()

    cursor = connection.execute(
        """
        SELECT schedule_id, day_of_week, start_time, end_time
        FROM class_schedules
        WHERE class_id = ?
        ORDER BY day_of_week, start_time
        """,
        (class_id,)
    )

    schedules = cursor.fetchall()
    connection.close()

    return schedules

def enroll_student(student_id: int, class_id: int) -> bool:
    connection = create_connection()

    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO student_classes
        (student_id, class_id)
        VALUES (?, ?)
        """,
        (student_id, class_id)
    )

    connection.commit()
    enrolled = cursor.rowcount == 1
    connection.close()

    return enrolled

def get_student_classes(student_id: int):
    connection = create_connection()

    cursor = connection.execute(
        """
        SELECT
            classes.class_id,
            classes.class_name
        FROM student_classes
        JOIN classes
            ON student_classes.class_id = classes.class_id
        WHERE student_classes.student_id = ?
        ORDER BY classes.class_name
        """,
        (student_id,)
    )

    classes = cursor.fetchall()
    connection.close()

    return classes

def get_class_students(class_id: int):
    connection = create_connection()

    cursor = connection.execute(
        """
        SELECT
            students.student_id,
            students.full_name,
            students.phone
        FROM student_classes
        JOIN students
            ON student_classes.student_id = students.student_id
        WHERE student_classes.class_id = ?
        ORDER BY students.full_name
        """,
        (class_id,)
    )

    students = cursor.fetchall()
    connection.close()

    return students



if __name__ == "__main__":
    load_dotenv()

    owner_id = int(os.getenv("OWNER_ID", "0"))

    if owner_id == 0:
        raise RuntimeError("OWNER_ID is missing from .env")

    create_admins_table()
    add_admin(owner_id, "owner")

    create_students_table()

    create_classes_table()

    create_class_schedules_table()

    create_student_classes_table()

    connection = create_connection()

    result = connection.execute(
        "PRAGMA foreign_keys"
    ).fetchone()
