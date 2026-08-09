"""
PostgreSQL Support — Drop-in replacement for SQLite
=====================================================
Uses PostgreSQL when DATABASE_URL is set, falls back to SQLite.
"""

import os
import json
import time
import uuid
import sqlite3
from typing import Any, Optional
from pathlib import Path


class Database:
    """Unified database interface — PostgreSQL or SQLite."""
    
    def __init__(self, db_path: str = "mermicorn.db"):
        self.database_url = os.environ.get("DATABASE_URL", "")
        self.db_path = db_path
        self._pg = None
        self._sqlite = None
        
        if self.database_url and "postgresql" in self.database_url:
            self._init_pg()
        else:
            self._init_sqlite()
    
    def _init_pg(self):
        """Initialize PostgreSQL connection."""
        try:
            import psycopg2
            self._pg = psycopg2.connect(self.database_url)
            self._pg.autocommit = True
            self._create_pg_tables()
        except ImportError:
            print("⚠️  psycopg2 not installed, falling back to SQLite")
            self._init_sqlite()
        except Exception as e:
            print(f"⚠️  PostgreSQL connection failed: {e}, falling back to SQLite")
            self._init_sqlite()
    
    def _init_sqlite(self):
        """Initialize SQLite connection."""
        self._sqlite = sqlite3.connect(self.db_path)
        self._sqlite.row_factory = sqlite3.Row
        self._create_sqlite_tables()
    
    def _create_pg_tables(self):
        """Create PostgreSQL tables."""
        cur = self._pg.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                role TEXT DEFAULT 'user',
                created_at REAL DEFAULT EXTRACT(EPOCH FROM NOW())
            )
        """)
        for table in ["coins", "vehicles", "deals", "champions", "products"]:
            if table == "coins":
                cols = "id TEXT PRIMARY KEY, name TEXT, year INTEGER, grade TEXT, price REAL, owner_id TEXT, created_at REAL"
            elif table == "vehicles":
                cols = "id TEXT PRIMARY KEY, year INTEGER, make TEXT, model TEXT, price REAL, mileage INTEGER, owner_id TEXT, created_at REAL"
            elif table == "deals":
                cols = "id TEXT PRIMARY KEY, destination TEXT, price REAL, dates TEXT, source TEXT, owner_id TEXT, created_at REAL"
            elif table == "champions":
                cols = "id TEXT PRIMARY KEY, name TEXT, tier TEXT, win_rate REAL, owner_id TEXT, created_at REAL"
            elif table == "products":
                cols = "id TEXT PRIMARY KEY, name TEXT, price REAL, description TEXT, tags TEXT, owner_id TEXT, created_at REAL"
            cur.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols})")
    
    def _create_sqlite_tables(self):
        """Create SQLite tables."""
        cur = self._sqlite.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, username TEXT UNIQUE, email TEXT,
            password_hash TEXT, api_key TEXT UNIQUE, role TEXT DEFAULT 'user',
            created_at REAL)""")
        self._sqlite.commit()
    
    def execute(self, query: str, params: tuple = ()) -> Any:
        """Execute a query."""
        if self._pg:
            cur = self._pg.cursor()
            cur.execute(query, params)
            if cur.description:
                return cur.fetchall()
            return cur.rowcount
        else:
            cur = self._sqlite.cursor()
            cur.execute(query, params)
            self._sqlite.commit()
            if cur.description:
                return cur.fetchall()
            return cur.rowcount
    
    def fetchone(self, query: str, params: tuple = ()) -> Optional[dict]:
        """Fetch one row."""
        if self._pg:
            cur = self._pg.cursor()
            cur.execute(query, params)
            row = cur.fetchone()
            if row:
                return dict(zip([d[0] for d in cur.description], row))
            return None
        else:
            cur = self._sqlite.cursor()
            cur.execute(query, params)
            row = cur.fetchone()
            if row:
                return dict(row)
            return None
    
    def fetchall(self, query: str, params: tuple = ()) -> list[dict]:
        """Fetch all rows."""
        if self._pg:
            cur = self._pg.cursor()
            cur.execute(query, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        else:
            cur = self._sqlite.cursor()
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]
    
    def commit(self):
        if self._sqlite:
            self._sqlite.commit()
    
    def close(self):
        if self._pg:
            self._pg.close()
        if self._sqlite:
            self._sqlite.close()
