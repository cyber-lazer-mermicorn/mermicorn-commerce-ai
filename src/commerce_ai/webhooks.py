"""
Webhooks — Event-Driven Marketplace Integration
=================================================
Register webhooks, receive events, trigger actions.
"""

import os
import json
import time
import hashlib
import hmac
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from collections import defaultdict


@dataclass
class Webhook:
    id: str
    url: str
    events: list[str]
    secret: str
    user_id: str = ""
    active: bool = True
    created_at: float = field(default_factory=time.time)
    last_triggered: float = 0
    failure_count: int = 0


class WebhookService:
    """Webhook management and delivery."""
    
    def __init__(self):
        self._webhooks: dict[str, Webhook] = {}
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._events: list[dict] = []
    
    def register(self, url: str, events: list[str], user_id: str = "", secret: str = "") -> Webhook:
        """Register a new webhook."""
        webhook_id = hashlib.sha256(f"{url}:{time.time()}".encode()).hexdigest()[:16]
        wh = Webhook(
            id=webhook_id, url=url, events=events,
            secret=secret or os.urandom(32).hex(),
            user_id=user_id,
        )
        self._webhooks[webhook_id] = wh
        return wh
    
    def unregister(self, webhook_id: str):
        """Remove a webhook."""
        self._webhooks.pop(webhook_id, None)
    
    def on(self, event: str, handler: Callable):
        """Register an event handler."""
        self._handlers[event].append(handler)
    
    def emit(self, event: str, data: dict = None):
        """Emit an event to all matching webhooks and handlers."""
        payload = {
            "event": event,
            "data": data or {},
            "timestamp": time.time(),
        }
        self._events.append(payload)
        if len(self._events) > 1000:
            self._events = self._events[-500:]
        
        # Call registered handlers
        for handler in self._handlers.get(event, []):
            try:
                handler(payload)
            except Exception:
                pass
        
        # Deliver to webhooks
        for wh in self._webhooks.values():
            if wh.active and event in wh.events:
                self._deliver(wh, payload)
    
    def _deliver(self, wh: Webhook, payload: dict):
        """Deliver webhook to endpoint."""
        try:
            body = json.dumps(payload).encode()
            signature = hmac.new(wh.secret.encode(), body, hashlib.sha256).hexdigest()
            
            req = urllib.request.Request(
                wh.url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                    "X-Webhook-Event": payload["event"],
                },
                method="POST",
            )
            urllib.request.urlopen(req, timeout=10)
            wh.last_triggered = time.time()
            wh.failure_count = 0
        except Exception:
            wh.failure_count += 1
            if wh.failure_count > 5:
                wh.active = False
    
    def list_webhooks(self, user_id: str = "") -> list[dict]:
        """List webhooks."""
        whs = self._webhooks.values()
        if user_id:
            whs = [w for w in whs if w.user_id == user_id]
        return [
            {"id": w.id, "url": w.url, "events": w.events, "active": w.active,
             "last_triggered": w.last_triggered, "failure_count": w.failure_count}
            for w in whs
        ]
    
    def get_recent_events(self, limit: int = 50) -> list[dict]:
        return self._events[-limit:]


webhook_service = WebhookService()
