import sqlite3
from datetime import datetime
from pathlib import Path

class Memory:
    def __init__(self, db_path: Path = None):
        if db_path is None:
            db_path = Path.home() / "jarvis_memory.db"
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_tables()
    
    def _init_tables(self):
        # المحادثات
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                task TEXT,
                action TEXT,
                result TEXT,
                provider TEXT,
                success INTEGER DEFAULT 1
            )
        """)
        # المشاريع
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                created_at TEXT
            )
        """)
        # الملخصات (للضغط)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS summary (
                id INTEGER PRIMARY KEY,
                content TEXT
            )
        """)
        # سجل التدقيق
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                actor TEXT,
                action TEXT,
                resource TEXT,
                context TEXT,
                status TEXT,
                error TEXT
            )
        """)
        # FTS5 للبحث السريع
        try:
            self.conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts
                USING fts5(task, result, content=conversations, content_rowid=id)
            """)
        except:
            pass
        self.conn.commit()
    
    def save(self, task, action, result, provider="local", success=1):
        self.conn.execute(
            "INSERT INTO conversations (timestamp, task, action, result, provider, success) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), task, action, result[:500], provider, success)
        )
        # FTS update
        try:
            lid = self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            self.conn.execute(
                "INSERT INTO memory_fts (rowid, task, result) VALUES (?, ?, ?)",
                (lid, task, result[:500])
            )
        except:
            pass
        self.conn.commit()
    
    def audit(self, action, resource, context, status, error=""):
        self.conn.execute(
            "INSERT INTO audit_log (timestamp, actor, action, resource, context, status, error) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), "jarvis_ai", action, resource, context, status, error)
        )
        self.conn.commit()
    
    def get_recent(self, n=10):
        return self.conn.execute(
            "SELECT task, action, result, provider FROM conversations ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
    
    def save_project(self, name, desc):
        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO projects (name, description, created_at) VALUES (?, ?, ?)",
                (name, desc, datetime.now().isoformat())
            )
            self.conn.commit()
            return True
        except:
            return False
    
    def get_projects(self):
        return self.conn.execute("SELECT name, description FROM projects ORDER BY created_at DESC").fetchall()
    
    def get_audit_log(self, n=50):
        return self.conn.execute(
            "SELECT timestamp, action, resource, status, error FROM audit_log ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
