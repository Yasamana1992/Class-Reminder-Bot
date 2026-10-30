import sqlite3
import os
from dotenv import load_dotenv

DB_NAME = "class_reminder.db"

def create_conection():
    connection = sqlite3.connect(DB_NAME)
    return connection

def create_admins_table():
    connection = create_conection()

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
    
    connection = create_conection()

    cursor = connection.execute(
        "INSERT OR IGNORE INTO admins(user_id, role) VALUES (?, ?)",
        (user_id, role)
    )    

    connection.commit()
    added = cursor.rowcount == 1
    connection.close()

    return added

def get_admin_role(user_id: int):
    connection = create_conection()

    result = connection.execute(
        "SELECT role FROM admins WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    connection.close()

    if result is None:
        return None

    return result[0]

def remove_admin(user_id: int) -> bool:
    conection = create_conection()

    cursor = conection.execute(
        "DELETE FROM admins WHERE user_id = ? AND role = ?",
        (user_id, "admin")
    )

    conection.commit()
    removed = cursor.rowcount == 1
    conection.close()

    return removed

if __name__ == "__main__":
    load_dotenv()

    owner_id = int(os.getenv("OWNER_ID", "0"))

    if owner_id == 0:
        raise RuntimeError("OWNER_ID is missing from .env")

    create_admins_table()
    add_admin(owner_id, "owner")

    print("Owner saved successfully!")