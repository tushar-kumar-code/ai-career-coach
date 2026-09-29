import smtplib
import ssl
import logging
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)


def _create_html_email_template(
    email: str,
    otp_code: str,
    purpose: str = "register"
) -> str:
    """
    Creates a premium, responsive HTML email matching Deep Navy + Warm Beige branding.
    Purpose: 'register', 'reset', 'login'
    """
    if purpose == "register":
        title = "Verify Your Email Address"
        subtitle = "Thank you for creating an account with AI Career Coach. Please use the verification code below to verify your email and activate your account."
        action_text = "Account Verification Code"
    elif purpose == "reset":
        title = "Password Reset Verification"
        subtitle = "We received a request to reset the password for your AI Career Coach account. Use the one-time code below to proceed with resetting your password."
        action_text = "Password Reset Code"
    else:
        title = "Sign-In Verification Code"
        subtitle = "Use the one-time 2FA verification code below to securely sign in to your AI Career Coach account."
        action_text = "2FA Login Code"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{title}</title>
      <style>
        body {{
          margin: 0;
          padding: 0;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
          background-color: #FAF8F3;
          color: #273444;
          -webkit-font-smoothing: antialiased;
        }}
        .wrapper {{
          width: 100%;
          table-layout: fixed;
          background-color: #FAF8F3;
          padding: 40px 0;
        }}
        .container {{
          max-width: 540px;
          margin: 0 auto;
          background: #FFFFFF;
          border-radius: 20px;
          border: 1px solid #E7E2D8;
          box-shadow: 0 4px 20px rgba(23, 50, 77, 0.06);
          overflow: hidden;
        }}
        .header {{
          background-color: #17324D;
          padding: 32px 36px;
          text-align: center;
        }}
        .brand-logo {{
          font-size: 22px;
          font-weight: 800;
          color: #FFFFFF;
          letter-spacing: -0.5px;
        }}
        .brand-logo span {{
          color: #B89B72;
        }}
        .brand-tag {{
          font-size: 12px;
          color: #A8B3C2;
          margin-top: 4px;
          letter-spacing: 0.5px;
          text-transform: uppercase;
        }}
        .content {{
          padding: 36px;
        }}
        .title {{
          font-size: 22px;
          font-weight: 700;
          color: #17324D;
          margin: 0 0 12px 0;
          text-align: center;
        }}
        .subtitle {{
          font-size: 14px;
          line-height: 1.6;
          color: #64748B;
          margin: 0 0 28px 0;
          text-align: center;
        }}
        .code-box {{
          background: #FAF8F3;
          border: 2px dashed #B89B72;
          border-radius: 16px;
          padding: 24px;
          text-align: center;
          margin: 0 0 28px 0;
        }}
        .code-label {{
          font-size: 11px;
          font-weight: 700;
          color: #17324D;
          text-transform: uppercase;
          letter-spacing: 1px;
          margin-bottom: 8px;
        }}
        .otp-code {{
          font-size: 36px;
          font-weight: 800;
          letter-spacing: 8px;
          color: #17324D;
          font-family: 'Courier New', Courier, monospace;
          margin: 0;
        }}
        .expiry-note {{
          font-size: 12px;
          color: #94A3B8;
          margin-top: 8px;
        }}
        .security-warning {{
          background: #F8FAFC;
          border-left: 3px solid #17324D;
          padding: 14px 16px;
          border-radius: 0 8px 8px 0;
          font-size: 12px;
          line-height: 1.5;
          color: #64748B;
          margin-bottom: 24px;
        }}
        .footer {{
          padding: 24px 36px;
          background: #FAF8F3;
          border-top: 1px solid #E7E2D8;
          text-align: center;
          font-size: 11px;
          color: #94A3B8;
          line-height: 1.5;
        }}
        .footer a {{
          color: #17324D;
          text-decoration: none;
        }}
      </style>
    </head>
    <body>
      <div class="wrapper">
        <table class="container" cellpadding="0" cellspacing="0" width="100%">
          <tr>
            <td class="header">
              <div class="brand-logo">AI <span>Career Coach</span></div>
              <div class="brand-tag">Autonomous Career Intelligence Platform</div>
            </td>
          </tr>
          <tr>
            <td class="content">
              <h1 class="title">{title}</h1>
              <p class="subtitle">{subtitle}</p>
              
              <div class="code-box">
                <div class="code-label">{action_text}</div>
                <div class="otp-code">{otp_code}</div>
                <div class="expiry-note">⏱️ Valid for 10 minutes. Never share this code.</div>
              </div>

              <div class="security-warning">
                <strong>Security Notice:</strong> If you did not initiate this request on AI Career Coach, please ignore this email or update your account security settings. No one from our team will ever ask you for your code.
              </div>
            </td>
          </tr>
          <tr>
            <td class="footer">
              This is an automated security email from AI Career Coach.<br>
              &copy; AI Career Coach. All rights reserved.
            </td>
          </tr>
        </table>
      </div>
    </body>
    </html>
    """
    return html_content


def _send_smtp_email_sync(
    to_email: str,
    subject: str,
    html_body: str,
    plain_text: str
) -> bool:
    """Synchronous SMTP email sender called inside async worker thread."""
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            f"[SMTP NOT CONFIGURED] Email to {to_email} not dispatched via network. "
            f"Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD in backend/.env to send real emails."
        )
        return False

    sender_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
    sender_name = settings.SMTP_FROM_NAME or "AI Career Coach"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = to_email

    part1 = MIMEText(plain_text, "plain")
    part2 = MIMEText(html_body, "html")
    msg.attach(part1)
    msg.attach(part2)

    try:
        if settings.SMTP_SSL:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context, timeout=15) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(sender_email, to_email, msg.as_string())
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                if settings.SMTP_TLS:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(sender_email, to_email, msg.as_string())

        logger.info(f"✅ Real verification email successfully sent to {to_email} via SMTP ({settings.SMTP_HOST})")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to deliver email to {to_email} via SMTP: {e}")
        return False


async def send_verification_email(
    to_email: str,
    otp_code: str,
    purpose: str = "register"
) -> Dict[str, Any]:
    """
    Asynchronously sends real OTP verification email to user's registered inbox.
    Returns: { "sent": bool, "status": str }
    """
    subjects = {
        "register": f"{otp_code} is your AI Career Coach email verification code",
        "reset": f"{otp_code} is your AI Career Coach password reset code",
        "login": f"{otp_code} is your AI Career Coach 2FA login code",
    }
    subject = subjects.get(purpose, f"{otp_code} is your AI Career Coach verification code")
    
    plain_text = f"Your AI Career Coach verification code is: {otp_code}\n\nThis code expires in 10 minutes. Please do not share it with anyone."
    html_body = _create_html_email_template(to_email, otp_code, purpose)

    # Dispatch to non-blocking worker thread
    is_sent = await asyncio.to_thread(
        _send_smtp_email_sync,
        to_email,
        subject,
        html_body,
        plain_text
    )

    return {
        "sent": is_sent,
        "email": to_email,
        "purpose": purpose
    }


def _create_login_success_html_template(
    email: str,
    user_name: Optional[str] = None,
    login_method: str = "Email/Password",
    login_time: Optional[str] = None
) -> str:
    """Creates a responsive, high-security HTML login alert email."""
    name_display = user_name or email.split("@")[0].title() or "Valued Candidate"
    time_display = login_time or "Just now"

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Successful Login Notification</title>
      <style>
        body {{
          margin: 0;
          padding: 0;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
          background-color: #0b1320;
          color: #f1f5f9;
        }}
        .wrapper {{
          width: 100%;
          table-layout: fixed;
          background-color: #0b1320;
          padding: 40px 0;
        }}
        .container {{
          max-width: 560px;
          margin: 0 auto;
          background: #111e33;
          border-radius: 16px;
          border: 1px solid #1e293b;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
          overflow: hidden;
        }}
        .header {{
          background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
          padding: 28px 32px;
          text-align: center;
          border-bottom: 1px solid #334155;
        }}
        .logo {{
          font-size: 22px;
          font-weight: 800;
          color: #38bdf8;
          letter-spacing: -0.5px;
        }}
        .logo span {{
          color: #f8fafc;
        }}
        .content {{
          padding: 32px;
        }}
        .badge {{
          display: inline-block;
          background: rgba(34, 197, 94, 0.15);
          color: #4ade80;
          border: 1px solid rgba(34, 197, 94, 0.3);
          border-radius: 20px;
          font-size: 12px;
          font-weight: 700;
          padding: 4px 14px;
          margin-bottom: 16px;
        }}
        .title {{
          font-size: 20px;
          font-weight: 700;
          color: #ffffff;
          margin: 0 0 10px 0;
        }}
        .subtitle {{
          font-size: 14px;
          color: #94a3b8;
          line-height: 1.6;
          margin-bottom: 24px;
        }}
        .details-card {{
          background: #0b1320;
          border: 1px solid #1e293b;
          border-radius: 12px;
          padding: 18px 20px;
          margin-bottom: 24px;
        }}
        .detail-row {{
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          font-size: 13px;
          border-bottom: 1px solid #1e293b;
        }}
        .detail-row:last-child {{
          border-bottom: none;
        }}
        .detail-label {{
          color: #64748b;
          font-weight: 500;
        }}
        .detail-value {{
          color: #f1f5f9;
          font-weight: 600;
        }}
        .btn {{
          display: block;
          background: #0284c7;
          color: #ffffff !important;
          text-align: center;
          text-decoration: none;
          font-weight: 700;
          font-size: 14px;
          padding: 12px 24px;
          border-radius: 8px;
          margin: 24px 0 16px 0;
        }}
        .footer {{
          font-size: 12px;
          color: #64748b;
          line-height: 1.5;
          border-top: 1px solid #1e293b;
          padding-top: 18px;
        }}
      </style>
    </head>
    <body>
      <div class="wrapper">
        <div class="container">
          <div class="header">
            <div class="logo">AI Career Coach <span>Twin</span></div>
          </div>
          <div class="content">
            <div class="badge">Security Notice: Active Session</div>
            <h1 class="title">Successful Login Notification</h1>
            <p class="subtitle">Hello <strong>{name_display}</strong>, your account was successfully accessed on AI Career Coach platform.</p>
            
            <div class="details-card">
              <div class="detail-row">
                <span class="detail-label">Account Email</span>
                <span class="detail-value">{email}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Sign-in Method</span>
                <span class="detail-value">{login_method}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Status</span>
                <span class="detail-value" style="color: #4ade80;">Authenticated Successfully</span>
              </div>
            </div>

            <p style="font-size: 13px; color: #94a3b8; margin: 0 0 16px 0;">
              If this was you, you can safely ignore this email. If you did not log in, please secure your account immediately.
            </p>

            <div class="footer">
              This is an automated security notification from AI Career Coach. Please do not reply to this email.
            </div>
          </div>
        </div>
      </div>
    </body>
    </html>
    """


async def send_login_success_email(
    to_email: str,
    user_name: Optional[str] = None,
    login_method: str = "Email/Password"
) -> Dict[str, Any]:
    """
    Sends a security notification email alert whenever a user successfully logs in.
    Dispatched non-blockingly via worker thread.
    """
    if not to_email or "@" not in to_email or to_email.endswith("@firebase.local"):
        return {"sent": False, "reason": "invalid_email"}

    subject = "Security Alert: Successful Login to AI Career Coach"
    plain_text = (
        f"Hello {user_name or 'there'},\n\n"
        f"You have successfully logged in to your AI Career Coach account via {login_method}.\n\n"
        f"If this was you, no action is needed.\n"
        f"If you did not initiate this login, please secure your account immediately.\n\n"
        f"- AI Career Coach Team"
    )
    html_body = _create_login_success_html_template(
        email=to_email,
        user_name=user_name,
        login_method=login_method
    )

    is_sent = await asyncio.to_thread(
        _send_smtp_email_sync,
        to_email,
        subject,
        html_body,
        plain_text
    )

    return {
        "sent": is_sent,
        "email": to_email,
        "type": "login_success_alert"
    }
