"""
Email Notifications — SendGrid + SMTP Fallback
================================================
Deal alerts, price drops, account notifications.
"""

import os
import json
import urllib.request
from typing import Optional
from dataclasses import dataclass


@dataclass
class Email:
    to: str
    subject: str
    html: str
    text: str = ""


class EmailService:
    """Multi-provider email service."""
    
    def __init__(self):
        self.sendgrid_key = os.environ.get("SENDGRID_API_KEY", "")
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_pass = os.environ.get("SMTP_PASS", "")
        self.from_email = os.environ.get("FROM_EMAIL", "noreply@mermicorn.dev")
        self.from_name = os.environ.get("FROM_NAME", "Mermicorn")
    
    def send(self, email: Email) -> dict:
        """Send email via best available provider."""
        if self.sendgrid_key:
            return self._send_sendgrid(email)
        elif self.smtp_user:
            return self._send_smtp(email)
        else:
            return {"success": False, "error": "No email provider configured"}
    
    def _send_sendgrid(self, email: Email) -> dict:
        """Send via SendGrid API."""
        payload = json.dumps({
            "personalizations": [{"to": [{"email": email.to}]}],
            "from": {"email": self.from_email, "name": self.from_name},
            "subject": email.subject,
            "content": [
                {"type": "text/plain", "value": email.text or email.html},
                {"type": "text/html", "value": email.html},
            ],
        }).encode()
        
        req = urllib.request.Request(
            "https://api.sendgrid.com/v3/mail/send",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.sendgrid_key}",
                "Content-Type": "application/json",
            },
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return {"success": True, "status": resp.status}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _send_smtp(self, email: Email) -> dict:
        """Send via SMTP."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = email.subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = email.to
            msg.attach(MIMEText(email.text or email.html, "plain"))
            msg.attach(MIMEText(email.html, "html"))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.sendmail(self.from_email, email.to, msg.as_string())
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ── Templates ──────────────────────────────────────────────
    
    def deal_alert(self, to: str, destination: str, price: float, dates: str, score: int):
        """Send deal alert email."""
        html = f"""
        <div style="font-family:Inter,sans-serif;max-width:600px;margin:0 auto;background:#0a0a0f;color:#e0e0e0;padding:40px;border-radius:16px">
            <h1 style="color:#a855f7;font-size:24px">🔥 Hot Deal Found!</h1>
            <div style="background:#1a1a2e;border-radius:12px;padding:24px;margin:20px 0">
                <h2 style="margin:0;color:#fff">{destination}</h2>
                <p style="color:#a855f7;font-size:32px;font-weight:bold;margin:10px 0">${price:.0f}</p>
                <p style="color:#888">{dates}</p>
            </div>
            <div style="text-align:center;margin:20px 0">
                <span style="background:#22c55e;color:#fff;padding:8px 24px;border-radius:8px;font-weight:bold">
                    Score: {score}/100
                </span>
            </div>
            <p style="color:#666;font-size:12px;text-align:center">Powered by Mermicorn AI</p>
        </div>
        """
        return self.send(Email(to=to, subject=f"🔥 {destination} — ${price:.0f}", html=html))
    
    def price_drop(self, to: str, item_name: str, old_price: float, new_price: float):
        """Send price drop alert."""
        drop = ((old_price - new_price) / old_price) * 100
        html = f"""
        <div style="font-family:Inter,sans-serif;max-width:600px;margin:0 auto;background:#0a0a0f;color:#e0e0e0;padding:40px;border-radius:16px">
            <h1 style="color:#22c55e;font-size:24px">📉 Price Drop!</h1>
            <div style="background:#1a1a2e;border-radius:12px;padding:24px;margin:20px 0">
                <h2 style="margin:0;color:#fff">{item_name}</h2>
                <p style="color:#666;text-decoration:line-through;font-size:20px">${old_price:.2f}</p>
                <p style="color:#22c55e;font-size:32px;font-weight:bold;margin:0">${new_price:.2f}</p>
                <p style="color:#22c55e">↓ {drop:.0f}% off</p>
            </div>
            <p style="color:#666;font-size:12px;text-align:center">Powered by Mermicorn AI</p>
        </div>
        """
        return self.send(Email(to=to, subject=f"📉 {item_name} dropped {drop:.0f}%", html=html))
    
    def welcome(self, to: str, username: str):
        """Send welcome email."""
        html = f"""
        <div style="font-family:Inter,sans-serif;max-width:600px;margin:0 auto;background:#0a0a0f;color:#e0e0e0;padding:40px;border-radius:16px">
            <h1 style="color:#a855f7;font-size:24px">Welcome to Mermicorn! 🍒</h1>
            <p>Hey {username},</p>
            <p>Your AI-powered business platform is ready.</p>
            <div style="background:#1a1a2e;border-radius:12px;padding:24px;margin:20px 0">
                <h3 style="color:#a855f7;margin:0 0 10px">Get Started:</h3>
                <ul style="color:#ccc">
                    <li>🛍️ Add products to your shop</li>
                    <li>🪙 Track your coin collection</li>
                    <li>🚗 Match your dream car</li>
                    <li>✈️ Find travel deals</li>
                    <li>⚔️ Build your game strategy</li>
                </ul>
            </div>
            <p style="color:#666;font-size:12px;text-align:center">Powered by Mermicorn AI</p>
        </div>
        """
        return self.send(Email(to=to, subject="Welcome to Mermicorn! 🍒", html=html))


email_service = EmailService()
