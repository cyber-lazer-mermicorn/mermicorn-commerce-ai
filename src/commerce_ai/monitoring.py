"""
Monitoring & Observability — Structured Logging + Metrics
==========================================================
Prometheus-compatible metrics, structured JSON logs, health checks.
"""

import os
import time
import json
import logging
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from pathlib import Path


class StructuredLogger:
    """JSON structured logger with rotation."""
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # JSON file handler
        fh = logging.FileHandler(self.log_dir / f"{name}.jsonl")
        fh.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(fh)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(message)s"))
        self.logger.addHandler(ch)
    
    def _emit(self, level: str, message: str, **kwargs):
        entry = {
            "ts": time.time(),
            "level": level,
            "service": self.name,
            "msg": message,
            **kwargs,
        }
        self.logger.log(
            logging.INFO if level == "info" else logging.WARNING if level == "warn" else logging.ERROR,
            json.dumps(entry),
        )
    
    def info(self, msg: str, **kw): self._emit("info", msg, **kw)
    def warn(self, msg: str, **kw): self._emit("warn", msg, **kw)
    def error(self, msg: str, **kw): self._emit("error", msg, **kw)


class Metrics:
    """Prometheus-compatible metrics collector."""
    
    def __init__(self):
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._start_time = time.time()
        self._lock = threading.Lock()
    
    def inc(self, name: str, value: int = 1):
        with self._lock:
            self._counters[name] += value
    
    def set(self, name: str, value: float):
        with self._lock:
            self._gauges[name] = value
    
    def observe(self, name: str, value: float):
        with self._lock:
            self._histograms[name].append(value)
            if len(self._histograms[name]) > 1000:
                self._histograms[name] = self._histograms[name][-500:]
    
    def to_prometheus(self) -> str:
        lines = []
        for name, val in sorted(self._counters.items()):
            lines.append(f"mermicorn_{name}_total {val}")
        for name, val in sorted(self._gauges.items()):
            lines.append(f"mermicorn_{name} {val}")
        for name, vals in sorted(self._histograms.items()):
            if vals:
                lines.append(f"mermicorn_{name}_count {len(vals)}")
                lines.append(f"mermicorn_{name}_sum {sum(vals):.2f}")
                lines.append(f"mermicorn_{name}_avg {sum(vals)/len(vals):.2f}")
        lines.append(f"mermicorn_uptime_seconds {time.time() - self._start_time:.0f}")
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {k: {"count": len(v), "avg": sum(v)/len(v) if v else 0, "p95": sorted(v)[int(len(v)*0.95)] if v else 0} for k, v in self._histograms.items()},
            "uptime": time.time() - self._start_time,
        }


# Global instances
logger = StructuredLogger("mermicorn")
metrics = Metrics()
