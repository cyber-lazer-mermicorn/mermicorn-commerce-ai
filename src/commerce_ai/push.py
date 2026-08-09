"""
Push Notifications — PWA Web Push
===================================
Send push notifications to subscribed browsers.
"""

import os
import json
import base64
import hashlib
import urllib.request
from dataclasses import dataclass
from typing import Optional


@dataclass
class PushSubscription:
    endpoint: str
    keys: dict
    user_id: str = ""
    created_at: float = 0


class PushNotificationService:
    """Web Push Notification service (VAPID)."""
    
    def __init__(self):
        self.vapid_public = os.environ.get("VAPID_PUBLIC_KEY", "")
        self.vapid_private = os.environ.get("VAPID_PRIVATE_KEY", "")
        self.vapid_claims = {
            "sub": os.environ.get("VAPID_EMAIL", "mailto:push@mermicorn.dev"),
        }
        self._subscriptions: list[PushSubscription] = []
    
    def is_configured(self) -> bool:
        return bool(self.vapid_public and self.vapid_private)
    
    def subscribe(self, subscription: PushSubscription):
        """Register a push subscription."""
        self._subscriptions.append(subscription)
    
    def unsubscribe(self, endpoint: str):
        """Remove a push subscription."""
        self._subscriptions = [s for s in self._subscriptions if s.endpoint != endpoint]
    
    def send(self, title: str, body: str, url: str = "/", data: dict = None) -> dict:
        """Send push notification to all subscribers."""
        if not self.is_configured():
            return {"success": False, "error": "VAPID not configured"}
        
        payload = json.dumps({"title": title, "body": body, "url": url, "data": data or {}})
        sent = 0
        errors = 0
        
        for sub in self._subscriptions:
            try:
                self._send_push(sub, payload)
                sent += 1
            except Exception:
                errors += 1
                self._subscriptions = [s for s in self._subscriptions if s.endpoint != sub.endpoint]
        
        return {"success": True, "sent": sent, "errors": errors, "total_subscribers": len(self._subscriptions)}
    
    def _send_push(self, sub: PushSubscription, payload: str):
        """Send push to a single subscription."""
        # In production, use py-vapid + requests
        # This is the minimal implementation
        headers = {
            "Content-Type": "application/octet-stream",
            "TTL": "86400",
        }
        req = urllib.request.Request(
            sub.endpoint,
            data=payload.encode(),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            pass
    
    def get_vapid_public_key(self) -> str:
        """Get VAPID public key for client."""
        return self.vapid_public


push_service = PushNotificationService()
