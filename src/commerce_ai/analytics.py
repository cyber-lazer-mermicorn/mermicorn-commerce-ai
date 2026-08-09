"""
Analytics — Usage Stats & Intelligence
========================================
Track user behavior, feature usage, and business metrics.
"""

import os
import time
import json
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


class AnalyticsService:
    """Usage analytics and business intelligence."""
    
    def __init__(self, db_path: str = "mermicorn.db"):
        self.db_path = db_path
        self._init_db()
        self._events: list[dict] = []
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS analytics_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT, user_id TEXT, properties TEXT, timestamp REAL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS analytics_metrics (
            name TEXT, value REAL, timestamp REAL, PRIMARY KEY (name, timestamp))""")
        conn.commit()
        conn.close()
    
    def track(self, event: str, user_id: str = "", properties: dict = None):
        """Track an event."""
        entry = {
            "event": event,
            "user_id": user_id,
            "properties": properties or {},
            "timestamp": time.time(),
        }
        self._events.append(entry)
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("INSERT INTO analytics_events (event, user_id, properties, timestamp) VALUES (?, ?, ?, ?)",
                    (event, user_id, json.dumps(properties or {}), time.time()))
        conn.commit()
        conn.close()
    
    def metric(self, name: str, value: float):
        """Record a metric."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("INSERT INTO analytics_metrics (name, value, timestamp) VALUES (?, ?, ?)",
                    (name, value, time.time()))
        conn.commit()
        conn.close()
    
    def get_events(self, event: str = None, user_id: str = None, limit: int = 100) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        query = "SELECT event, user_id, properties, timestamp FROM analytics_events WHERE 1=1"
        params = []
        
        if event:
            query += " AND event = ?"
            params.append(event)
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cur.execute(query, params)
        events = [
            {"event": r[0], "user_id": r[1], "properties": json.loads(r[2] or "{}"), "timestamp": r[3]}
            for r in cur.fetchall()
        ]
        conn.close()
        return events
    
    def get_summary(self, days: int = 7) -> dict:
        """Get analytics summary for last N days."""
        cutoff = time.time() - (days * 86400)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Event counts
        cur.execute("SELECT event, COUNT(*) FROM analytics_events WHERE timestamp > ? GROUP BY event", (cutoff,))
        events = dict(cur.fetchall())
        
        # Active users
        cur.execute("SELECT COUNT(DISTINCT user_id) FROM analytics_events WHERE timestamp > ? AND user_id != ''", (cutoff,))
        active_users = cur.fetchone()[0]
        
        # Total events
        cur.execute("SELECT COUNT(*) FROM analytics_events WHERE timestamp > ?", (cutoff,))
        total_events = cur.fetchone()[0]
        
        # Top users
        cur.execute("SELECT user_id, COUNT(*) as cnt FROM analytics_events WHERE timestamp > ? AND user_id != '' GROUP BY user_id ORDER BY cnt DESC LIMIT 10", (cutoff,))
        top_users = [{"user_id": r[0], "events": r[1]} for r in cur.fetchall()]
        
        conn.close()
        
        return {
            "period_days": days,
            "total_events": total_events,
            "active_users": active_users,
            "events_by_type": events,
            "top_users": top_users,
        }
    
    def get_daily_stats(self, days: int = 30) -> list[dict]:
        """Get daily event counts."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT date(timestamp, 'unixepoch') as day, COUNT(*) as cnt
            FROM analytics_events
            WHERE timestamp > ?
            GROUP BY day ORDER BY day
        """, (time.time() - days * 86400,))
        
        stats = [{"date": r[0], "count": r[1]} for r in cur.fetchall()]
        conn.close()
        return stats


analytics = AnalyticsService()
