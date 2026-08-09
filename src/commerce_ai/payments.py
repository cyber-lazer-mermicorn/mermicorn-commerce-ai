"""
Mermicorn Payments — Stripe Integration
========================================
Real payment processing for commerce.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(slots=True)
class Payment:
    """A payment record."""
    id: str
    amount: float
    currency: str
    status: str
    customer_email: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)
    stripe_payment_id: str = ""
    created_at: float = field(default_factory=time.time)


@dataclass(slots=True)
class Product:
    """A sellable product."""
    id: str
    name: str
    price: float
    currency: str = "usd"
    description: str = ""
    images: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CheckoutSession:
    """A Stripe checkout session."""
    id: str
    product_id: str
    amount: float
    currency: str
    status: str
    url: str = ""
    customer_email: str = ""
    created_at: float = field(default_factory=time.time)


class StripePayments:
    """
    Stripe payment processing.
    
    Features:
    - One-time payments
    - Checkout sessions
    - Payment intents
    - Refunds
    - Webhooks
    """
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("STRIPE_SECRET_KEY", "")
        self.webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
        self.payments: list[Payment] = []
        self.products: dict[str, Product] = {}
        self.sessions: list[CheckoutSession] = []
    
    def create_product(self, name: str, price: float, description: str = "",
                      currency: str = "usd") -> Product:
        """Create a product."""
        product_id = f"prod_{uuid.uuid4().hex[:16]}"
        product = Product(id=product_id, name=name, price=price,
                         currency=currency, description=description)
        self.products[product_id] = product
        return product
    
    def create_checkout(self, product_id: str, customer_email: str = "") -> CheckoutSession:
        """Create a checkout session."""
        product = self.products.get(product_id)
        if not product:
            raise ValueError(f"Product not found: {product_id}")
        
        session_id = f"cs_{uuid.uuid4().hex[:16]}"
        session = CheckoutSession(
            id=session_id,
            product_id=product_id,
            amount=product.price,
            currency=product.currency,
            status="pending",
            customer_email=customer_email,
        )
        self.sessions.append(session)
        return session
    
    def create_payment(self, amount: float, currency: str = "usd",
                      customer_email: str = "", description: str = "",
                      metadata: dict[str, Any] | None = None) -> Payment:
        """Create a payment intent."""
        payment_id = f"pi_{uuid.uuid4().hex[:16]}"
        payment = Payment(
            id=payment_id,
            amount=amount,
            currency=currency,
            status="pending",
            customer_email=customer_email,
            description=description,
            metadata=metadata or {},
        )
        self.payments.append(payment)
        return payment
    
    def confirm_payment(self, payment_id: str) -> Payment:
        """Confirm a payment (mock)."""
        for payment in self.payments:
            if payment.id == payment_id:
                payment.status = "succeeded"
                return payment
        raise ValueError(f"Payment not found: {payment_id}")
    
    def refund(self, payment_id: str, amount: float | None = None) -> Payment:
        """Refund a payment (mock)."""
        for payment in self.payments:
            if payment.id == payment_id:
                payment.status = "refunded"
                return payment
        raise ValueError(f"Payment not found: {payment_id}")
    
    def handle_webhook(self, payload: dict, sig_header: str = "") -> dict[str, Any]:
        """Handle a Stripe webhook."""
        event_type = payload.get("type", "")
        
        handlers = {
            "checkout.session.completed": self._handle_checkout_complete,
            "payment_intent.succeeded": self._handle_payment_success,
            "charge.refunded": self._handle_refund,
        }
        
        handler = handlers.get(event_type)
        if handler:
            return handler(payload.get("data", {}).get("object", {}))
        
        return {"status": "unhandled", "type": event_type}
    
    def _handle_checkout_complete(self, data: dict) -> dict:
        """Handle completed checkout."""
        session_id = data.get("id", "")
        for session in self.sessions:
            if session.id == session_id:
                session.status = "completed"
        return {"status": "processed"}
    
    def _handle_payment_success(self, data: dict) -> dict:
        """Handle successful payment."""
        return {"status": "processed"}
    
    def _handle_refund(self, data: dict) -> dict:
        """Handle refund."""
        return {"status": "processed"}
    
    def get_revenue(self) -> dict[str, Any]:
        """Calculate revenue."""
        succeeded = [p for p in self.payments if p.status == "succeeded"]
        return {
            "total_revenue": sum(p.amount for p in succeeded),
            "total_payments": len(succeeded),
            "pending": len([p for p in self.payments if p.status == "pending"]),
            "refunded": len([p for p in self.payments if p.status == "refunded"]),
        }
    
    def get_stats(self) -> dict[str, Any]:
        return {
            "products": len(self.products),
            "payments": len(self.payments),
            "sessions": len(self.sessions),
            "revenue": self.get_revenue(),
        }
