"""Email service — SendGrid/SMTP sending, templates, verification flow."""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

logger = logging.getLogger("dark_factory")

TEMPLATES: dict[str, str] = {}


def configure():
    _load_templates()


def _load_templates():
    base = os.path.join(os.path.dirname(__file__), "..", "templates")
    for fname in ["welcome.html", "verify.html", "reset.html", "receipt.html", "notification.html"]:
        path = os.path.join(base, fname)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                TEMPLATES[fname.replace(".html", "")] = f.read()


def render(template_name: str, **vars: str) -> str | None:
    t = TEMPLATES.get(template_name)
    if not t:
        return None
    for k, v in vars.items():
        t = t.replace(f"{{{{{k}}}}}", v)
    return t


async def send_sendgrid(to: str, subject: str, html: str, api_key: str) -> dict:
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        message = Mail(Email(os.environ.get("FROM_EMAIL", "noreply@example.com")), To(to), subject, Content("text/html", html))
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        return {"success": response.status_code in (200, 201, 202), "status": response.status_code}
    except Exception as e:
        logger.warning("SendGrid send failed: %s", e)
        return {"success": False, "error": str(e)}


async def send_smtp(to: str, subject: str, html: str, host: str, port: int, user: str, passwd: str) -> dict:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = os.environ.get("FROM_EMAIL", "noreply@example.com")
        msg["To"] = to
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, passwd)
            s.send_message(msg)
        return {"success": True}
    except Exception as e:
        logger.warning("SMTP send failed: %s", e)
        return {"success": False, "error": str(e)}


async def send_email(to: str, subject: str, html: str) -> dict:
    api_key = os.environ.get("SENDGRID_API_KEY", "")
    if api_key:
        return await send_sendgrid(to, subject, html, api_key)
    host = os.environ.get("SMTP_HOST", "")
    if host:
        return await send_smtp(
            to, subject, html, host,
            int(os.environ.get("SMTP_PORT", "587")),
            os.environ.get("SMTP_USER", ""),
            os.environ.get("SMTP_PASS", ""),
        )
    logger.info("Email not configured — would send to %s: %s", to, subject)
    return {"success": True, "dry_run": True, "message": f"Email disabled (set SENDGRID_API_KEY or SMTP_HOST)"}


async def send_verification(email: str, token: str, verify_url: str) -> dict:
    html = render("verify", token=token, email=email, verify_url=verify_url)
    if not html:
        html = f"<p>Verify your email: <a href='{verify_url}?token={token}'>{verify_url}?token={token}</a></p>"
    return await send_email(email, "Verify your email address", html)


async def send_welcome(email: str, name: str) -> dict:
    html = render("welcome", name=name, email=email)
    if not html:
        html = f"<h2>Welcome, {name}!</h2><p>Thanks for joining.</p>"
    return await send_email(email, "Welcome!", html)
