"""
Mermicorn Production Stack — FastAPI + SQLite + Auth + Logging
=============================================================
Shared infrastructure for all verticals.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

# ════════════════════════════════════════════════════════════════
# DATABASE
# ════════════════════════════════════════════════════════════════

class Database:
    """SQLite database with auto-migration."""
    
    def __init__(self, db_path: str = "./data/mermicorn.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_tables()
    
    def _init_tables(self):
        """Initialize database tables."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                api_key TEXT UNIQUE,
                role TEXT DEFAULT 'user',
                created_at REAL,
                last_login REAL
            );
            
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id),
                key TEXT UNIQUE NOT NULL,
                name TEXT,
                permissions TEXT DEFAULT 'read',
                rate_limit INTEGER DEFAULT 60,
                created_at REAL,
                expires_at REAL,
                last_used REAL
            );
            
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action TEXT,
                resource TEXT,
                details TEXT,
                ip_address TEXT,
                timestamp REAL
            );
            
            CREATE TABLE IF NOT EXISTS rate_limits (
                key TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0,
                window_start REAL
            );
        """)
        self.conn.commit()
    
    @contextmanager
    def cursor(self):
        """Get a database cursor."""
        cur = self.conn.cursor()
        try:
            yield cur
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query."""
        with self.cursor() as cur:
            return cur.execute(query, params)
    
    def fetch_one(self, query: str, params: tuple = ()) -> dict | None:
        """Fetch a single row."""
        with self.cursor() as cur:
            row = cur.execute(query, params).fetchone()
            return dict(row) if row else None
    
    def fetch_all(self, query: str, params: tuple = ()) -> list[dict]:
        """Fetch all rows."""
        with self.cursor() as cur:
            return [dict(row) for row in cur.execute(query, params).fetchall()]
    
    def close(self):
        self.conn.close()


# ════════════════════════════════════════════════════════════════
# AUTH
# ════════════════════════════════════════════════════════════════

class AuthService:
    """JWT + API key authentication."""
    
    def __init__(self, db: Database, secret: str = "mermicorn-secret-change-me"):
        self.db = db
        self.secret = secret
    
    def hash_password(self, password: str) -> str:
        return hashlib.sha256(f"{self.secret}:{password}".encode()).hexdigest()
    
    def create_user(self, username: str, email: str, password: str,
                   role: str = "user") -> dict:
        """Create a new user."""
        user_id = str(uuid.uuid4())
        api_key = f"mk_{uuid.uuid4().hex[:32]}"
        
        self.db.execute(
            "INSERT INTO users (id, username, email, password_hash, api_key, role, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, email, self.hash_password(password), api_key, role, time.time())
        )
        
        return {"id": user_id, "username": username, "api_key": api_key, "role": role}
    
    def authenticate(self, username: str, password: str) -> dict | None:
        """Authenticate with username/password."""
        user = self.db.fetch_one(
            "SELECT * FROM users WHERE username = ? AND password_hash = ?",
            (username, self.hash_password(password))
        )
        if user:
            self.db.execute("UPDATE users SET last_login = ? WHERE id = ?", (time.time(), user["id"]))
            return {"id": user["id"], "username": user["username"], "role": user["role"]}
        return None
    
    def verify_api_key(self, api_key: str) -> dict | None:
        """Verify an API key."""
        # Check user api_key
        user = self.db.fetch_one("SELECT * FROM users WHERE api_key = ?", (api_key,))
        if user:
            return {"id": user["id"], "username": user["username"], "role": user["role"]}
        
        # Check dedicated api_keys
        key_data = self.db.fetch_one("SELECT * FROM api_keys WHERE key = ?", (api_key,))
        if key_data:
            self.db.execute("UPDATE api_keys SET last_used = ? WHERE key = ?", (time.time(), api_key))
            user = self.db.fetch_one("SELECT * FROM users WHERE id = ?", (key_data["user_id"],))
            if user:
                return {"id": user["id"], "username": user["username"], "role": user["role"],
                       "permissions": key_data["permissions"]}
        
        return None
    
    def create_api_key(self, user_id: str, name: str, permissions: str = "read") -> dict:
        """Create a new API key for a user."""
        key_id = str(uuid.uuid4())
        key = f"mk_{uuid.uuid4().hex[:32]}"
        
        self.db.execute(
            "INSERT INTO api_keys (id, user_id, key, name, permissions, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (key_id, user_id, key, name, permissions, time.time())
        )
        
        return {"id": key_id, "key": key, "name": name, "permissions": permissions}
    
    def log_audit(self, user_id: str, action: str, resource: str,
                 details: str = "", ip_address: str = "") -> None:
        """Log an audit event."""
        self.db.execute(
            "INSERT INTO audit_log (user_id, action, resource, details, ip_address, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, action, resource, details, ip_address, time.time())
        )


# ════════════════════════════════════════════════════════════════
# RATE LIMITER
# ════════════════════════════════════════════════════════════════

class RateLimiter:
    """Sliding window rate limiter."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def check(self, key: str, limit: int = 60, window: int = 60) -> bool:
        """Check if request is allowed."""
        now = time.time()
        
        with self.db.cursor() as cur:
            row = cur.execute("SELECT * FROM rate_limits WHERE key = ?", (key,)).fetchone()
            
            if not row:
                cur.execute("INSERT INTO rate_limits (key, count, window_start) VALUES (?, 1, ?)",
                          (key, now))
                return True
            
            row = dict(row)
            if now - row["window_start"] > window:
                cur.execute("UPDATE rate_limits SET count = 1, window_start = ? WHERE key = ?",
                          (now, key))
                return True
            
            if row["count"] >= limit:
                return False
            
            cur.execute("UPDATE rate_limits SET count = count + 1 WHERE key = ?", (key,))
            return True


# ════════════════════════════════════════════════════════════════
# LOGGER
# ════════════════════════════════════════════════════════════════

class StructuredLogger:
    """JSON structured logging."""
    
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'
        ))
        self.logger.addHandler(handler)
    
    def info(self, message: str, **kwargs):
        extra = json.dumps(kwargs) if kwargs else ""
        self.logger.info(f"{message} {extra}")
    
    def error(self, message: str, **kwargs):
        extra = json.dumps(kwargs) if kwargs else ""
        self.logger.error(f"{message} {extra}")
    
    def warning(self, message: str, **kwargs):
        extra = json.dumps(kwargs) if kwargs else ""
        self.logger.warning(f"{message} {extra}")


# ════════════════════════════════════════════════════════════════
# PRODUCTION STACK
# ════════════════════════════════════════════════════════════════

class MermicornStack:
    """
    Complete production stack for any vertical.
    
    Usage:
        stack = MermicornStack("numismatic")
        # stack.db — database
        # stack.auth — authentication
        # stack.rate_limiter — rate limiting
        # stack.logger — structured logging
    """
    
    def __init__(self, service_name: str, db_path: str | None = None):
        self.service_name = service_name
        self.secret = os.environ.get("MERMICORN_SECRET", f"{service_name}-secret-change-me")
        
        db_path = db_path or f"./data/{service_name}.db"
        self.db = Database(db_path)
        self.auth = AuthService(self.db, self.secret)
        self.rate_limiter = RateLimiter(self.db)
        self.logger = StructuredLogger(service_name)
    
    def check_rate_limit(self, api_key: str, limit: int = 60) -> bool:
        """Check rate limit for an API key."""
        return self.rate_limiter.check(f"api:{api_key}", limit)
    
    def log_request(self, user_id: str, method: str, path: str,
                   status: int, duration_ms: float) -> None:
        """Log an API request."""
        self.logger.info("request", method=method, path=path, status=status,
                        duration_ms=round(duration_ms, 2), user_id=user_id)
    
    def get_stats(self) -> dict[str, Any]:
        """Get service statistics."""
        return {
            "service": self.service_name,
            "db_path": str(self.db.db_path),
            "users": len(self.db.fetch_all("SELECT id FROM users")),
            "api_keys": len(self.db.fetch_all("SELECT id FROM api_keys")),
            "audit_entries": len(self.db.fetch_all("SELECT id FROM audit_log")),
        }
