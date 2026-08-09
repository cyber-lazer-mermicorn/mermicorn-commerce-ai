"""
Database Backup & Recovery — Automated Backups
================================================
SQLite and PostgreSQL backup with rotation.
"""

import os
import shutil
import sqlite3
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime


class BackupManager:
    """Automated database backup with rotation."""
    
    def __init__(self, db_path: str = "mermicorn.db", backup_dir: str = "backups"):
        self.db_path = db_path
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.max_backups = int(os.environ.get("BACKUP_MAX", "30"))
        self.database_url = os.environ.get("DATABASE_URL", "")
    
    def backup(self) -> dict:
        """Create a backup."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.database_url and "postgresql" in self.database_url:
            return self._backup_postgres(timestamp)
        else:
            return self._backup_sqlite(timestamp)
    
    def _backup_sqlite(self, timestamp: str) -> dict:
        """SQLite backup using .backup API."""
        backup_path = self.backup_dir / f"mermicorn_{timestamp}.db"
        try:
            conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(str(backup_path))
            conn.backup(backup_conn)
            backup_conn.close()
            conn.close()
            
            size = backup_path.stat().st_size
            self._rotate()
            return {"success": True, "path": str(backup_path), "size": size, "timestamp": timestamp}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _backup_postgres(self, timestamp: str) -> dict:
        """PostgreSQL backup using pg_dump."""
        backup_path = self.backup_dir / f"mermicorn_{timestamp}.sql"
        try:
            result = subprocess.run(
                ["pg_dump", self.database_url],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                backup_path.write_text(result.stdout)
                size = backup_path.stat().st_size
                self._rotate()
                return {"success": True, "path": str(backup_path), "size": size, "timestamp": timestamp}
            else:
                return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def restore(self, backup_path: str) -> dict:
        """Restore from backup."""
        try:
            if backup_path.endswith(".sql"):
                subprocess.run(["psql", self.database_url, "-f", backup_path], check=True, timeout=300)
            else:
                shutil.copy2(backup_path, self.db_path)
            return {"success": True, "restored_from": backup_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_backups(self) -> list[dict]:
        """List available backups."""
        backups = []
        for f in sorted(self.backup_dir.glob("mermicorn_*"), reverse=True):
            backups.append({
                "name": f.name,
                "path": str(f),
                "size": f.stat().st_size,
                "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
        return backups
    
    def _rotate(self):
        """Keep only max_backups most recent."""
        files = sorted(self.backup_dir.glob("mermicorn_*"), key=lambda f: f.stat().st_mtime)
        while len(files) > self.max_backups:
            files.pop(0).unlink()
