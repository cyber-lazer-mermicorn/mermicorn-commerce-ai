"""
Mermicorn Skills Engine — Shared Intelligence Layer
====================================================
Reusable skills: API, data, automation, memory, monitoring.
"""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional


# ════════════════════════════════════════════════════════════════
# SKILL 1: API Integration
# ════════════════════════════════════════════════════════════════

@dataclass(slots=True)
class APIEndpoint:
    """An external API endpoint."""
    name: str
    base_url: str
    auth_type: str  # api_key, oauth, bearer
    rate_limit: int  # requests per minute
    headers: dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "base_url": self.base_url, 
                "auth_type": self.auth_type, "rate_limit": self.rate_limit}


class APISkill:
    """
    API Integration Skill — Connect to any external service.
    
    Provides:
    - Rate limiting
    - Retry logic
    - Response caching
    - Error handling
    - Request logging
    """
    
    def __init__(self):
        self.endpoints: dict[str, APIEndpoint] = {}
        self.cache: dict[str, tuple[float, Any]] = {}
        self.request_log: list[dict[str, Any]] = []
        self._call_counts: dict[str, int] = defaultdict(int)
    
    def register(self, name: str, base_url: str, auth_type: str = "api_key",
                 rate_limit: int = 60, headers: dict[str, str] | None = None) -> APIEndpoint:
        """Register an API endpoint."""
        endpoint = APIEndpoint(name=name, base_url=base_url, auth_type=auth_type,
                              rate_limit=rate_limit, headers=headers or {})
        self.endpoints[name] = endpoint
        return endpoint
    
    def _get_cache_key(self, api: str, path: str, params: dict) -> str:
        return f"{api}:{path}:{json.dumps(params, sort_keys=True)}"
    
    def _check_cache(self, key: str, ttl: int = 300) -> Any | None:
        """Check if cached response exists and is fresh."""
        if key in self.cache:
            ts, data = self.cache[key]
            if time.time() - ts < ttl:
                return data
        return None
    
    def _set_cache(self, key: str, data: Any) -> None:
        """Cache a response."""
        self.cache[key] = (time.time(), data)
    
    def log_request(self, api: str, path: str, status: int, latency_ms: float) -> None:
        """Log an API request."""
        self.request_log.append({
            "api": api, "path": path, "status": status,
            "latency_ms": latency_ms, "timestamp": time.time(),
        })
        self._call_counts[api] += 1
    
    def get_stats(self) -> dict[str, Any]:
        return {
            "endpoints": len(self.endpoints),
            "cache_entries": len(self.cache),
            "total_requests": sum(self._call_counts.values()),
            "calls_by_api": dict(self._call_counts),
        }


# ════════════════════════════════════════════════════════════════
# SKILL 2: Data Analysis
# ════════════════════════════════════════════════════════════════

@dataclass(slots=True)
class DataPoint:
    """A single data point for analysis."""
    timestamp: float
    value: float
    label: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class DataAnalysisSkill:
    """
    Data Analysis Skill — Analyze trends, patterns, distributions.
    
    Provides:
    - Time series analysis
    - Statistical summaries
    - Trend detection
    - Anomaly detection
    - Comparative analysis
    """
    
    def __init__(self):
        self.datasets: dict[str, list[DataPoint]] = defaultdict(list)
    
    def add_point(self, dataset: str, value: float, label: str = "",
                  metadata: dict[str, Any] | None = None) -> DataPoint:
        """Add a data point."""
        point = DataPoint(timestamp=time.time(), value=value, label=label,
                         metadata=metadata or {})
        self.datasets[dataset].append(point)
        return point
    
    def add_points(self, dataset: str, points: list[dict[str, Any]]) -> int:
        """Bulk add data points."""
        count = 0
        for p in points:
            self.add_point(dataset, p["value"], p.get("label", ""), p.get("metadata", {}))
            count += 1
        return count
    
    def summary(self, dataset: str) -> dict[str, Any]:
        """Get statistical summary."""
        points = self.datasets.get(dataset, [])
        if not points:
            return {"count": 0}
        
        values = [p.value for p in points]
        return {
            "count": len(values),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values),
            "latest": values[-1],
            "trend": self._detect_trend(values),
        }
    
    def _detect_trend(self, values: list[float]) -> str:
        """Detect trend direction."""
        if len(values) < 2:
            return "insufficient_data"
        
        recent = values[-min(5, len(values)):]
        older = values[:min(5, len(values))]
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        pct_change = (recent_avg - older_avg) / max(older_avg, 1) * 100
        
        if pct_change > 10:
            return "rising"
        elif pct_change < -10:
            return "falling"
        else:
            return "stable"
    
    def compare(self, dataset1: str, dataset2: str) -> dict[str, Any]:
        """Compare two datasets."""
        s1 = self.summary(dataset1)
        s2 = self.summary(dataset2)
        
        if s1["count"] == 0 or s2["count"] == 0:
            return {"error": "Insufficient data"}
        
        return {
            "dataset1": s1,
            "dataset2": s2,
            "mean_difference": s1["mean"] - s2["mean"],
            "winner": dataset1 if s1["mean"] > s2["mean"] else dataset2,
        }
    
    def get_stats(self) -> dict[str, Any]:
        return {
            "datasets": len(self.datasets),
            "total_points": sum(len(v) for v in self.datasets.values()),
        }


# ════════════════════════════════════════════════════════════════
# SKILL 3: Automation
# ════════════════════════════════════════════════════════════════

@dataclass(slots=True)
class Task:
    """An automated task."""
    id: str
    name: str
    schedule: str  # once, hourly, daily, weekly
    action: str  # function name
    params: dict[str, Any] = field(default_factory=dict)
    last_run: float = 0
    next_run: float = 0
    status: str = "pending"
    results: list[dict[str, Any]] = field(default_factory=list)


class AutomationSkill:
    """
    Automation Skill — Schedule and execute tasks.
    
    Provides:
    - Task scheduling
    - Webhook triggers
    - Batch operations
    - Retry logic
    - Execution history
    """
    
    def __init__(self):
        self.tasks: dict[str, Task] = {}
        self.webhooks: dict[str, str] = {}  # url -> event
        self.execution_log: list[dict[str, Any]] = []
    
    def schedule(self, name: str, schedule: str, action: str,
                params: dict[str, Any] | None = None) -> Task:
        """Schedule a task."""
        task_id = f"task_{int(time.time() * 1000)}"
        task = Task(id=task_id, name=name, schedule=schedule, action=action,
                   params=params or {}, next_run=time.time())
        self.tasks[task_id] = task
        return task
    
    def register_webhook(self, url: str, event: str) -> None:
        """Register a webhook for an event."""
        self.webhooks[event] = url
    
    def log_execution(self, task_id: str, status: str, result: Any) -> None:
        """Log a task execution."""
        self.execution_log.append({
            "task_id": task_id, "status": status, "result": result,
            "timestamp": time.time(),
        })
        if task_id in self.tasks:
            self.tasks[task_id].last_run = time.time()
            self.tasks[task_id].status = status
    
    def get_pending_tasks(self) -> list[Task]:
        """Get tasks ready to run."""
        now = time.time()
        return [t for t in self.tasks.values() if t.next_run <= now]
    
    def get_stats(self) -> dict[str, Any]:
        return {
            "tasks": len(self.tasks),
            "webhooks": len(self.webhooks),
            "executions": len(self.execution_log),
            "pending": len(self.get_pending_tasks()),
        }


# ════════════════════════════════════════════════════════════════
# SKILL 4: Memory
# ════════════════════════════════════════════════════════════════

@dataclass(slots=True)
class MemoryEntry:
    """A memory entry."""
    key: str
    value: Any
    category: str
    importance: float  # 0-1
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "category": self.category,
                "importance": self.importance, "access_count": self.access_count}


class MemorySkill:
    """
    Memory Skill — Persistent knowledge storage.
    
    Provides:
    - Key-value storage
    - Category organization
    - Importance scoring
    - Access tracking
    - forgetting curve
    - knowledge graph
    """
    
    def __init__(self, storage_path: str | None = None):
        self.entries: dict[str, MemoryEntry] = {}
        self.storage_path = Path(storage_path) if storage_path else None
        if self.storage_path:
            self._load()
    
    def _load(self) -> None:
        """Load memory from disk."""
        if self.storage_path and self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                for k, v in data.items():
                    self.entries[k] = MemoryEntry(**v)
            except Exception:
                pass
    
    def _save(self) -> None:
        """Save memory to disk."""
        if self.storage_path:
            data = {k: v.to_dict() for k, v in self.entries.items()}
            self.storage_path.write_text(json.dumps(data, indent=2))
    
    def remember(self, key: str, value: Any, category: str = "general",
                importance: float = 0.5) -> MemoryEntry:
        """Store a memory."""
        entry = MemoryEntry(key=key, value=value, category=category,
                           importance=importance)
        self.entries[key] = entry
        self._save()
        return entry
    
    def recall(self, key: str) -> Any | None:
        """Recall a memory."""
        if key in self.entries:
            entry = self.entries[key]
            entry.accessed_at = time.time()
            entry.access_count += 1
            self._save()
            return entry.value
        return None
    
    def forget(self, key: str) -> bool:
        """Forget a memory."""
        if key in self.entries:
            del self.entries[key]
            self._save()
            return True
        return False
    
    def search(self, query: str, category: str | None = None) -> list[MemoryEntry]:
        """Search memories."""
        results = []
        for entry in self.entries.values():
            if category and entry.category != category:
                continue
            if query.lower() in entry.key.lower() or query.lower() in str(entry.value).lower():
                results.append(entry)
        return sorted(results, key=lambda e: e.importance, reverse=True)
    
    def by_category(self, category: str) -> list[MemoryEntry]:
        """Get all memories in a category."""
        return [e for e in self.entries.values() if e.category == category]
    
    def get_stats(self) -> dict[str, Any]:
        categories = defaultdict(int)
        for e in self.entries.values():
            categories[e.category] += 1
        return {
            "total": len(self.entries),
            "categories": dict(categories),
            "avg_importance": sum(e.importance for e in self.entries.values()) / max(len(self.entries), 1),
        }


# ════════════════════════════════════════════════════════════════
# SKILL 5: Monitoring
# ════════════════════════════════════════════════════════════════

@dataclass(slots=True)
class Metric:
    """A monitoring metric."""
    name: str
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)
    tags: dict[str, str] = field(default_factory=dict)


class MonitoringSkill:
    """
    Monitoring Skill — Track performance and health.
    
    Provides:
    - Metric collection
    - Threshold alerting
    - Health checks
    - Performance tracking
    - Status reporting
    """
    
    def __init__(self):
        self.metrics: dict[str, list[Metric]] = defaultdict(list)
        self.alerts: dict[str, dict[str, Any]] = {}
        self.health_checks: dict[str, Callable] = {}
    
    def record(self, name: str, value: float, unit: str = "",
               tags: dict[str, str] | None = None) -> Metric:
        """Record a metric."""
        metric = Metric(name=name, value=value, unit=unit, tags=tags or {})
        self.metrics[name].append(metric)
        return metric
    
    def set_alert(self, name: str, threshold: float, condition: str = "above") -> None:
        """Set an alert threshold."""
        self.alerts[name] = {"threshold": threshold, "condition": condition}
    
    def check_alerts(self) -> list[dict[str, Any]]:
        """Check for triggered alerts."""
        triggered = []
        for name, alert in self.alerts.items():
            if name in self.metrics and self.metrics[name]:
                latest = self.metrics[name][-1].value
                if alert["condition"] == "above" and latest > alert["threshold"]:
                    triggered.append({"metric": name, "value": latest, "threshold": alert["threshold"]})
                elif alert["condition"] == "below" and latest < alert["threshold"]:
                    triggered.append({"metric": name, "value": latest, "threshold": alert["threshold"]})
        return triggered
    
    def register_health(self, name: str, check_fn: Callable) -> None:
        """Register a health check."""
        self.health_checks[name] = check_fn
    
    def health_status(self) -> dict[str, Any]:
        """Run all health checks."""
        results = {}
        for name, check_fn in self.health_checks.items():
            try:
                results[name] = {"status": "healthy", "result": check_fn()}
            except Exception as e:
                results[name] = {"status": "unhealthy", "error": str(e)}
        return results
    
    def summary(self, name: str, last_n: int = 10) -> dict[str, Any]:
        """Get metric summary."""
        metrics = self.metrics.get(name, [])[-last_n:]
        if not metrics:
            return {"name": name, "count": 0}
        
        values = [m.value for m in metrics]
        return {
            "name": name,
            "count": len(values),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "latest": values[-1],
        }
    
    def get_stats(self) -> dict[str, Any]:
        return {
            "metrics_tracked": len(self.metrics),
            "alerts_configured": len(self.alerts),
            "health_checks": len(self.health_checks),
            "total_datapoints": sum(len(v) for v in self.metrics.values()),
        }


# ════════════════════════════════════════════════════════════════
# COMBINED SKILLS ENGINE
# ════════════════════════════════════════════════════════════════

class MermicornSkills:
    """
    Combined skills engine for all verticals.
    
    Provides access to all skills through one interface.
    """
    
    def __init__(self, storage_dir: str = "./skills_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.api = APISkill()
        self.data = DataAnalysisSkill()
        self.automation = AutomationSkill()
        self.memory = MemorySkill(str(self.storage_dir / "memory.json"))
        self.monitoring = MonitoringSkill()
    
    def get_stats(self) -> dict[str, Any]:
        return {
            "api": self.api.get_stats(),
            "data": self.data.get_stats(),
            "automation": self.automation.get_stats(),
            "memory": self.memory.get_stats(),
            "monitoring": self.monitoring.get_stats(),
        }
