import sqlite3
import json
import os
from datetime import datetime, timedelta
import threading

class SQLiteStorage:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'faq_jobs.db')
        self._init_db()
        self.lock = threading.Lock()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    result TEXT,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
            ''')
            conn.commit()

    def store_result(self, job_id, result):
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                # Set expiration to 24 hours from now
                expires_at = datetime.now() + timedelta(hours=24)
                conn.execute(
                    'INSERT OR REPLACE INTO jobs (job_id, result, created_at, expires_at) VALUES (?, ?, ?, ?)',
                    (job_id, json.dumps(result), datetime.now().isoformat(), expires_at.isoformat())
                )
                conn.commit()

    def get_result(self, job_id):
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                # Clean up expired jobs first
                conn.execute(
                    'DELETE FROM jobs WHERE expires_at < ?',
                    (datetime.now().isoformat(),)
                )
                conn.commit()
                
                # Get the job result
                cursor = conn.execute(
                    'SELECT result FROM jobs WHERE job_id = ?',
                    (job_id,)
                )
                result = cursor.fetchone()
                return json.loads(result[0]) if result else None

    def delete_result(self, job_id):
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    'DELETE FROM jobs WHERE job_id = ?',
                    (job_id,)
                )
                conn.commit()

# Singleton instance
db = SQLiteStorage()