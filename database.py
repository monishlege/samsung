

import sqlite3
import pandas as pd

DB_NAME = "campus.db"


def create_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            complaint TEXT,
            category TEXT,
            priority TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    conn.commit()
    conn.close()


def add_complaint(name, complaint, category, priority):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO complaints (name, complaint, category, priority)
        VALUES (?, ?, ?, ?)
    """, (name, complaint, category, priority))

    conn.commit()
    conn.close()


def get_complaints():
    conn = sqlite3.connect(DB_NAME)

    df = pd.read_sql_query(
        "SELECT * FROM complaints ORDER BY id DESC",
        conn
    )

    conn.close()
    return df
