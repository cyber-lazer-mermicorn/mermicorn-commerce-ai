"""
Search — Full-Text Search Across All Data
==========================================
SQLite FTS5 full-text search with ranking.
"""

import sqlite3
import json
from typing import Any
from pathlib import Path


class SearchEngine:
    """Full-text search across all verticals."""
    
    def __init__(self, db_path: str = "mermicorn.db"):
        self.db_path = db_path
        self._init_fts()
    
    def _init_fts(self):
        """Initialize FTS5 virtual tables."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Create FTS tables
        for table, columns in [
            ("search_coins", "name year grade"),
            ("search_vehicles", "year make model"),
            ("search_deals", "destination dates source"),
            ("search_products", "name description tags"),
            ("search_champions", "name tier"),
        ]:
            cols = ", ".join(columns.split())
            cur.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS {table} 
                USING fts5(id, {cols}, content='', content_rowid='rowid')
            """)
        
        conn.commit()
        conn.close()
    
    def index_coins(self, db_path: str = None):
        """Index all coins."""
        conn = sqlite3.connect(db_path or self.db_path)
        cur = conn.cursor()
        
        cur.execute("DELETE FROM search_coins")
        cur.execute("SELECT id, name, year, grade FROM coins")
        for row in cur.fetchall():
            cur.execute(
                "INSERT INTO search_coins (id, name, year, grade) VALUES (?, ?, ?, ?)",
                (row[0], row[1], str(row[2]), row[3])
            )
        
        conn.commit()
        conn.close()
    
    def index_vehicles(self, db_path: str = None):
        """Index all vehicles."""
        conn = sqlite3.connect(db_path or self.db_path)
        cur = conn.cursor()
        
        cur.execute("DELETE FROM search_vehicles")
        cur.execute("SELECT id, year, make, model FROM vehicles")
        for row in cur.fetchall():
            cur.execute(
                "INSERT INTO search_vehicles (id, year, make, model) VALUES (?, ?, ?, ?)",
                (row[0], str(row[1]), row[2], row[3])
            )
        
        conn.commit()
        conn.close()
    
    def index_deals(self, db_path: str = None):
        """Index all deals."""
        conn = sqlite3.connect(db_path or self.db_path)
        cur = conn.cursor()
        
        cur.execute("DELETE FROM search_deals")
        cur.execute("SELECT id, destination, dates, source FROM deals")
        for row in cur.fetchall():
            cur.execute(
                "INSERT INTO search_deals (id, destination, dates, source) VALUES (?, ?, ?, ?)",
                (row[0], row[1], row[2], row[3])
            )
        
        conn.commit()
        conn.close()
    
    def index_products(self, db_path: str = None):
        """Index all products."""
        conn = sqlite3.connect(db_path or self.db_path)
        cur = conn.cursor()
        
        cur.execute("DELETE FROM search_products")
        cur.execute("SELECT id, name, description, tags FROM products")
        for row in cur.fetchall():
            cur.execute(
                "INSERT INTO search_products (id, name, description, tags) VALUES (?, ?, ?, ?)",
                (row[0], row[1], row[2] or "", row[3] or "")
            )
        
        conn.commit()
        conn.close()
    
    def index_all(self, db_path: str = None):
        """Reindex all data."""
        self.index_coins(db_path)
        self.index_vehicles(db_path)
        self.index_deals(db_path)
        self.index_products(db_path)
    
    def search(self, query: str, tables: list[str] = None) -> dict[str, list]:
        """Search across all or specific tables."""
        if not tables:
            tables = ["search_coins", "search_vehicles", "search_deals", "search_products", "search_champions"]
        
        results = {}
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        for table in tables:
            try:
                cur.execute(
                    f"SELECT id, rank FROM {table} WHERE {table} MATCH ? ORDER BY rank LIMIT 20",
                    (query,)
                )
                rows = cur.fetchall()
                results[table.replace("search_", "")] = [
                    {"id": row[0], "rank": row[1]} for row in rows
                ]
            except Exception:
                results[table.replace("search_", "")] = []
        
        conn.close()
        return results
    
    def suggest(self, prefix: str) -> list[str]:
        """Auto-suggest based on prefix."""
        suggestions = []
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        for table, column in [
            ("coins", "name"), ("vehicles", "make"), ("deals", "destination"), ("products", "name")
        ]:
            try:
                cur.execute(f"SELECT DISTINCT {column} FROM {table} WHERE {column} LIKE ? LIMIT 5", (f"%{prefix}%",))
                suggestions.extend([row[0] for row in cur.fetchall()])
            except Exception:
                pass
        
        conn.close()
        return suggestions[:10]


search_engine = SearchEngine()
