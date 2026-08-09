"""
Mermicorn WebSocket — Real-Time Updates
========================================
Live updates for dashboards and clients.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass(slots=True)
class WSClient:
    """A WebSocket client."""
    id: str
    user_id: str
    channels: set[str] = field(default_factory=set)
    connected_at: float = field(default_factory=time.time)
    last_ping: float = field(default_factory=time.time)


class WebSocketManager:
    """
    Manages WebSocket connections and real-time broadcasts.
    
    Usage:
        ws = WebSocketManager()
        ws.on("price_update", handle_price)  # register handler
        ws.broadcast("price_update", {"coin": "morgan", "price": 52})  # send to all
    """
    
    def __init__(self):
        self.clients: dict[str, WSClient] = {}
        self.handlers: dict[str, list[Callable]] = {}
        self.message_queue: list[dict] = []
        self.max_queue = 1000
    
    def connect(self, user_id: str, channels: list[str] | None = None) -> str:
        """Register a new client connection."""
        client_id = str(uuid.uuid4())
        client = WSClient(id=client_id, user_id=user_id,
                         channels=set(channels or ["global"]))
        self.clients[client_id] = client
        return client_id
    
    def disconnect(self, client_id: str) -> None:
        """Remove a client connection."""
        self.clients.pop(client_id, None)
    
    def subscribe(self, client_id: str, channel: str) -> None:
        """Subscribe to a channel."""
        if client_id in self.clients:
            self.clients[client_id].channels.add(channel)
    
    def unsubscribe(self, client_id: str, channel: str) -> None:
        """Unsubscribe from a channel."""
        if client_id in self.clients:
            self.clients[client_id].channels.discard(channel)
    
    def on(self, event: str, handler: Callable) -> None:
        """Register an event handler."""
        if event not in self.handlers:
            self.handlers[event] = []
        self.handlers[event].append(handler)
    
    def off(self, event: str, handler: Callable) -> None:
        """Remove an event handler."""
        if event in self.handlers:
            self.handlers[event] = [h for h in self.handlers[event] if h != handler]
    
    async def broadcast(self, channel: str, data: dict[str, Any]) -> int:
        """Broadcast to all clients on a channel."""
        message = {
            "type": channel,
            "data": data,
            "timestamp": time.time(),
        }
        
        # Queue message
        self.message_queue.append(message)
        if len(self.message_queue) > self.max_queue:
            self.message_queue = self.message_queue[-self.max_queue:]
        
        # Find subscribers
        count = 0
        for client in self.clients.values():
            if channel in client.channels or "global" in client.channels:
                count += 1
        
        # Trigger handlers
        for handler in self.handlers.get(channel, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception:
                pass
        
        return count
    
    async def broadcast_all(self, data: dict[str, Any]) -> int:
        """Broadcast to all connected clients."""
        return await self.broadcast("global", data)
    
    def get_channel_count(self, channel: str) -> int:
        """Count clients on a channel."""
        return sum(1 for c in self.clients.values() if channel in c.channels)
    
    def get_stats(self) -> dict[str, Any]:
        """Get WebSocket stats."""
        channels: dict[str, int] = {}
        for client in self.clients.values():
            for ch in client.channels:
                channels[ch] = channels.get(ch, 0) + 1
        
        return {
            "connected_clients": len(self.clients),
            "channels": channels,
            "handlers": len(self.handlers),
            "queued_messages": len(self.message_queue),
        }


# ════════════════════════════════════════════════════════════════
# EVENT TYPES
# ════════════════════════════════════════════════════════════════

class Events:
    """Standard event types."""
    # Coin events
    COIN_ADDED = "coin:added"
    COIN_UPDATED = "coin:updated"
    COIN_SOLD = "coin:sold"
    PRICE_ALERT = "coin:price_alert"
    
    # Vehicle events
    VEHICLE_ADDED = "vehicle:added"
    VEHICLE_SOLD = "vehicle:sold"
    MAINTENANCE_DUE = "vehicle:maintenance_due"
    
    # Travel events
    DEAL_FOUND = "travel:deal_found"
    PRICE_DROP = "travel:price_drop"
    ALERT_TRIGGERED = "travel:alert_triggered"
    
    # Rift events
    GAME_RECORDED = "rift:game_recorded"
    TIER_CHANGED = "rift:tier_changed"
    
    # Commerce events
    ORDER_PLACED = "commerce:order_placed"
    PAYMENT_RECEIVED = "commerce:payment_received"
    LISTING_CREATED = "commerce:listing_created"
    
    # System events
    USER_CONNECTED = "user:connected"
    USER_DISCONNECTED = "user:disconnected"
    SYSTEM_ALERT = "system:alert"
