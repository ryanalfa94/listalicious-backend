# app/services/mailer.py
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Optional

log = logging.getLogger("mailer")
log.setLevel(logging.INFO)

APP_URL = os.getenv("APP_URL", "http://localhost:3000")
ENV = (os.getenv("ENV", "dev") or "dev").lower()
EMAIL_FROM = os.getenv("EMAIL_FROM", "no-reply@example.com")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "")

# Brevo SMTP relay (free tier, no expiry) — takes priority over SendGrid when configured
BREVO_SMTP_LOGIN = os.getenv("BREVO_SMTP_LOGIN")
BREVO_SMTP_KEY = os.getenv("BREVO_SMTP_KEY")
BREVO_SMTP_HOST = os.getenv("BREVO_SMTP_HOST", "smtp-relay.brevo.com")
BREVO_SMTP_PORT = int(os.getenv("BREVO_SMTP_PORT", "587"))

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")


def _send_brevo_email(to_email: str, subject: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((EMAIL_FROM_NAME, EMAIL_FROM)) if EMAIL_FROM_NAME else EMAIL_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(BREVO_SMTP_HOST, BREVO_SMTP_PORT, timeout=10) as server:
        server.starttls()
        server.login(BREVO_SMTP_LOGIN, BREVO_SMTP_KEY)
        server.sendmail(EMAIL_FROM, [to_email], msg.as_string())


def _send_sendgrid_email_api(to_email: str, subject: str, html: str) -> None:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, From, To, Subject, HtmlContent

    message = Mail(
        from_email=From(EMAIL_FROM, EMAIL_FROM_NAME or None),
        to_emails=To(to_email),
        subject=Subject(subject),
        html_content=HtmlContent(html),
    )
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    resp = sg.send(message)
    if resp.status_code >= 300:
        log.warning("SendGrid non-2xx: %s %s", resp.status_code, getattr(resp, "body", b"")[:300])


def _send_sendgrid_email(to_email: str, subject: str, html: str) -> None:
    """
    Low-level helper to send email. Uses Brevo SMTP if configured, else SendGrid.
    In dev, if neither is configured, we log instead of failing.
    """
    has_brevo = bool(BREVO_SMTP_LOGIN and BREVO_SMTP_KEY)
    has_sendgrid = bool(SENDGRID_API_KEY)

    if ENV == "dev" and not has_brevo and not has_sendgrid:
        log.info("[dev] send email simulated -> to=%s subject=%s html=%s", to_email, subject, html)
        return

    if not has_brevo and not has_sendgrid:
        raise RuntimeError("No email provider configured (set BREVO_SMTP_LOGIN/BREVO_SMTP_KEY or SENDGRID_API_KEY)")

    if not EMAIL_FROM:
        raise RuntimeError("EMAIL_FROM not set (must be a verified sender or domain)")

    try:
        if has_brevo:
            _send_brevo_email(to_email, subject, html)
        else:
            _send_sendgrid_email_api(to_email, subject, html)
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

def send_email_change_verification(to_email: str, token: str) -> None:
    """
    Sends a verification email to the *new* address. Clicking the link confirms
    the change and replaces the user's email.
    """
    link = f"{APP_URL.rstrip('/')}/confirm-email-change?token={token}"
    subject = "Confirm your new email address"
    html = f"""
        <div style="font-family:system-ui,Segoe UI,Arial,sans-serif">
          <h2>Confirm your new email address</h2>
          <p>Click the button below to confirm this as your new email address.</p>
          <p><a href="{link}" style="display:inline-block;padding:10px 16px;border-radius:8px;background:#8b5cf6;color:#fff;text-decoration:none;">Confirm Email Change</a></p>
          <p>Or open this link: <br><a href="{link}">{link}</a></p>
          <p>If you didn't request this, you can safely ignore this email.</p>
        </div>
    """
    if ENV == "dev":
        log.info("[dev] email change confirmation link for %s: %s", to_email, link)
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
