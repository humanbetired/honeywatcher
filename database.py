import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "data", "honeywatcher.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS attack_log (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp     TEXT NOT NULL,
        service       TEXT NOT NULL,
        src_ip        TEXT NOT NULL,
        src_port      INTEGER,
        country       TEXT,
        city          TEXT,
        lat           REAL,
        lon           REAL,
        username      TEXT,
        password      TEXT,
        payload       TEXT,
        method        TEXT,
        path          TEXT,
        user_agent    TEXT,
        raw_data      TEXT
    );

        CREATE TABLE IF NOT EXISTS attacker_profile (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            src_ip        TEXT NOT NULL,
            first_seen    TEXT,
            last_seen     TEXT,
            total_attempts INTEGER DEFAULT 0,
            services_hit  TEXT,
            profile_type  TEXT,
            confidence    TEXT,
            ai_summary    TEXT,
            updated_at    TEXT
        );
    """)
    conn.commit()
    conn.close()
    print("[DB] Initialized")

if __name__ == "__main__":
    init_db()