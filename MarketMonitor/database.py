"""
=========================================================
Market Intelligence Monitor (MIM)
SQLite Database
=========================================================
"""

import sqlite3
from config import DATABASE_FILE


class Database:

    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_FILE)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS news(
            story_id TEXT PRIMARY KEY,
            headline TEXT,
            category TEXT,
            publish_time TEXT,
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports(
            report_id TEXT PRIMARY KEY,
            report_name TEXT,
            publish_time TEXT,
            pdf_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.conn.commit()

    def story_exists(self, story_id):

        self.cursor.execute(
            "SELECT 1 FROM news WHERE story_id=?",
            (story_id,)
        )

        return self.cursor.fetchone() is not None

    def save_story(self, story_id, headline, category, publish_time, url):

        self.cursor.execute("""
        INSERT OR IGNORE INTO news
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            story_id,
            headline,
            category,
            publish_time,
            url
        ))

        self.conn.commit()

    def close(self):
        self.conn.close()