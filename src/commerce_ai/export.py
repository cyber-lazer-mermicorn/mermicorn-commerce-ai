"""
Export/Import — CSV and JSON Data Export
=========================================
Export all user data in standard formats.
"""

import csv
import json
import io
import sqlite3
from typing import Any
from pathlib import Path


class ExportService:
    """Export data to CSV, JSON, or backup format."""
    
    def __init__(self, db_path: str = "mermicorn.db"):
        self.db_path = db_path
    
    def export_json(self, user_id: str) -> dict:
        """Export all user data as JSON."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        data = {"exported_at": __import__("time").time(), "user_id": user_id}
        
        for table in ["coins", "vehicles", "deals", "champions", "products"]:
            try:
                cur.execute(f"SELECT * FROM {table} WHERE owner_id = ?", (user_id,))
                data[table] = [dict(row) for row in cur.fetchall()]
            except Exception:
                data[table] = []
        
        conn.close()
        return data
    
    def export_csv(self, user_id: str, table: str) -> str:
        """Export a table as CSV."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        try:
            cur.execute(f"SELECT * FROM {table} WHERE owner_id = ?", (user_id,))
            rows = cur.fetchall()
            if not rows:
                return ""
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
            
            conn.close()
            return output.getvalue()
        except Exception:
            conn.close()
            return ""
    
    def export_all_csv(self, user_id: str) -> dict[str, str]:
        """Export all tables as CSV."""
        return {
            table: self.export_csv(user_id, table)
            for table in ["coins", "vehicles", "deals", "champions", "products"]
        }
    
    def import_json(self, user_id: str, data: dict) -> dict:
        """Import data from JSON."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        imported = {}
        
        for table in ["coins", "vehicles", "deals", "champions", "products"]:
            if table not in data:
                continue
            
            count = 0
            for item in data[table]:
                item["owner_id"] = user_id
                try:
                    cols = ", ".join(item.keys())
                    placeholders = ", ".join(["?"] * len(item))
                    cur.execute(f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})", list(item.values()))
                    count += 1
                except Exception:
                    pass
            
            imported[table] = count
        
        conn.commit()
        conn.close()
        return imported
    
    def import_csv(self, user_id: str, table: str, csv_data: str) -> int:
        """Import data from CSV."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        count = 0
        
        try:
            reader = csv.DictReader(io.StringIO(csv_data))
            for row in reader:
                row["owner_id"] = user_id
                cols = ", ".join(row.keys())
                placeholders = ", ".join(["?"] * len(row))
                cur.execute(f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})", list(row.values()))
                count += 1
        except Exception:
            pass
        
        conn.commit()
        conn.close()
        return count


export_service = ExportService()
