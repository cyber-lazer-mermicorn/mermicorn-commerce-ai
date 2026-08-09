"""
Multi-User — Teams, Sharing, Permissions
==========================================
Share data across users with role-based access.
"""

import os
import time
import uuid
import json
import sqlite3
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Team:
    id: str
    name: str
    owner_id: str
    created_at: float = field(default_factory=time.time)
    members: list = field(default_factory=list)


class TeamService:
    """Team management and sharing."""
    
    def __init__(self, db_path: str = "mermicorn.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS teams (
            id TEXT PRIMARY KEY, name TEXT, owner_id TEXT, created_at REAL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS team_members (
            team_id TEXT, user_id TEXT, role TEXT DEFAULT 'member', joined_at REAL,
            PRIMARY KEY (team_id, user_id))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS shares (
            id TEXT PRIMARY KEY, owner_id TEXT, target_user_id TEXT,
            resource_type TEXT, resource_id TEXT, permission TEXT DEFAULT 'view',
            created_at REAL)""")
        conn.commit()
        conn.close()
    
    def create_team(self, name: str, owner_id: str) -> Team:
        team_id = str(uuid.uuid4())[:8]
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("INSERT INTO teams (id, name, owner_id, created_at) VALUES (?, ?, ?, ?)",
                    (team_id, name, owner_id, time.time()))
        cur.execute("INSERT INTO team_members (team_id, user_id, role, joined_at) VALUES (?, ?, ?, ?)",
                    (team_id, owner_id, "owner", time.time()))
        conn.commit()
        conn.close()
        return Team(id=team_id, name=name, owner_id=owner_id)
    
    def add_member(self, team_id: str, user_id: str, role: str = "member") -> bool:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO team_members (team_id, user_id, role, joined_at) VALUES (?, ?, ?, ?)",
                        (team_id, user_id, role, time.time()))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()
    
    def remove_member(self, team_id: str, user_id: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM team_members WHERE team_id = ? AND user_id = ?", (team_id, user_id))
        conn.commit()
        conn.close()
    
    def get_user_teams(self, user_id: str) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT t.id, t.name, t.owner_id, tm.role 
            FROM teams t JOIN team_members tm ON t.id = tm.team_id 
            WHERE tm.user_id = ?
        """, (user_id,))
        teams = [{"id": r[0], "name": r[1], "owner_id": r[2], "role": r[3]} for r in cur.fetchall()]
        conn.close()
        return teams
    
    def share_resource(self, owner_id: str, target_user_id: str, resource_type: str, resource_id: str, permission: str = "view") -> str:
        share_id = str(uuid.uuid4())[:8]
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("INSERT INTO shares (id, owner_id, target_user_id, resource_type, resource_id, permission, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (share_id, owner_id, target_user_id, resource_type, resource_id, permission, time.time()))
        conn.commit()
        conn.close()
        return share_id
    
    def get_shared_with(self, user_id: str) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT * FROM shares WHERE target_user_id = ?", (user_id,))
        shares = [dict(zip(["id","owner_id","target_user_id","resource_type","resource_id","permission","created_at"], r)) for r in cur.fetchall()]
        conn.close()
        return shares
    
    def can_access(self, user_id: str, resource_type: str, resource_id: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM shares WHERE target_user_id = ? AND resource_type = ? AND resource_id = ?",
                    (user_id, resource_type, resource_id))
        result = cur.fetchone()
        conn.close()
        return result is not None


team_service = TeamService()
