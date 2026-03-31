# app/services/mailer.py
import os
import logging
from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, HtmlContent

log = logging.getLogger("mailer")
log.setLevel(logging.INFO)

APP_URL = os.getenv("APP_URL", "http://localhost:3000")
ENV = (os.getenv("ENV", "dev") or "dev").lower()
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "no-reply@example.com")

def _send_sendgrid_email(to_email: str, subject: str, html: str) -> None:
    """
    Low-level helper to send email via SendGrid.
    In dev, if SENDGRID_API_KEY is missing, we log instead of failing.
    """
    if ENV == "dev" and not SENDGRID_API_KEY:
        log.info("[dev] send email simulated -> to=%s subject=%s html=%s", to_email, subject, html)
        return

    if not SENDGRID_API_KEY:
        raise RuntimeError("SENDGRID_API_KEY not set")

    if not EMAIL_FROM:
        raise RuntimeError("EMAIL_FROM not set (must be a verified sender or domain in SendGrid)")

    message = Mail(
        from_email=From(EMAIL_FROM),
        to_emails=To(to_email),
        subject=Subject(subject),
        html_content=HtmlContent(html),
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        resp = sg.send(message)
        # 2xx or 202 is OK; otherwise log
        if resp.status_code >= 300:
            log.warning("SendGrid non-2xx: %s %s", resp.status_code, getattr(resp, "body", b"")[:300])
    except Exception as e:
        # In dev, just log; in prod, bubble up
        if ENV == "dev":
            log.exception("[dev] send email failed (logged only): %s", e)
        else:
            raise

def send_email_verification(to_email: str, token: str) -> None:
    """
    Sends a "verify your email" message with a link containing the token.
    """
    link = f"{APP_URL.rstrip('/')}/verify-email?token={token}"
    subject = "Verify your email"
    html = f"""
        <div style="font-family:system-ui,Segoe UI,Arial,sans-serif">
          <h2>Verify your email</h2>
          <p>Click the button below to verify your email address.</p>
          <p><a href="{link}" style="display:inline-block;padding:10px 16px;border-radius:8px;background:#0ea5e9;color:#fff;text-decoration:none;">Verify Email</a></p>
          <p>Or open this link: <br><a href="{link}">{link}</a></p>
          <p>If you didn’t request this, you can safely ignore this email.</p>
        </div>
    """
    # Always log the link in dev for quick testing
    if ENV == "dev":
        log.info("[dev] email verification link for %s: %s", to_email, link)
    _send_sendgrid_email(to_email, subject, html)

def send_password_reset(to_email: str, token: str) -> None:
    """
    Sends a password reset email with a link containing a one-time token.
    """
    link = f"{APP_URL.rstrip('/')}/reset-password?token={token}"
    subject = "Reset your password"
    html = f"""
        <div style="font-family:system-ui,Segoe UI,Arial,sans-serif">
          <h2>Reset your password</h2>
          <p>Click the button below to set a new password. This link will expire soon.</p>
          <p><a href="{link}" style="display:inline-block;padding:10px 16px;border-radius:8px;background:#22c55e;color:#fff;text-decoration:none;">Reset Password</a></p>
          <p>Or open this link: <br><a href="{link}">{link}</a></p>
          <p>If you didn’t request this, you can safely ignore this email.</p>
        </div>
    """
    if ENV == "dev":
        log.info("[dev] password reset link for %s: %s", to_email, link)
    _send_sendgrid_email(to_email, subject, html)
