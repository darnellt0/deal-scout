"""Email service for sending transactional emails."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """SMTP-based email service for sending transactional emails."""

    def __init__(self):
        """Initialize email service with SMTP configuration."""
        self.settings = get_settings()
        self.smtp_host = self.settings.smtp_host
        self.smtp_port = self.settings.smtp_port
        self.smtp_user = self.settings.smtp_user
        self.smtp_password = self.settings.smtp_password
        self.smtp_use_tls = self.settings.smtp_use_tls
        self.email_from = self.settings.email_from

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """
        Send email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email_from
            msg["To"] = to_email

            # Add text part if provided
            if text_body:
                msg.attach(MIMEText(text_body, "plain"))

            # Add HTML part
            msg.attach(MIMEText(html_body, "html"))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_password_reset_email(
        self,
        to_email: str,
        username: str,
        reset_token: str,
        reset_url: Optional[str] = None,
    ) -> bool:
        """
        Send password reset email.

        Args:
            to_email: User's email address
            username: User's username
            reset_token: Password reset token
            reset_url: Optional custom reset URL (will be appended with token)

        Returns:
            True if email sent successfully, False otherwise
        """
        if reset_url is None:
            reset_url = "https://app.deal-scout.local/reset-password"

        full_reset_url = f"{reset_url}?token={reset_token}"

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Password Reset Request</h2>
                <p>Hi {username},</p>
                <p>We received a request to reset your password. Click the button below to reset it.</p>
                <p>
                    <a href="{full_reset_url}"
                       style="background-color: #007bff; color: white; padding: 10px 20px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </p>
                <p>Or copy and paste this link in your browser:</p>
                <p><code>{full_reset_url}</code></p>
                <p style="color: #666; font-size: 12px;">
                    This link expires in 30 minutes. If you didn't request this, please ignore this email.
                </p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">Deal Scout Team</p>
            </body>
        </html>
        """

        text_body = f"""
        Password Reset Request

        Hi {username},

        We received a request to reset your password. Visit this link to reset it:

        {full_reset_url}

        This link expires in 30 minutes. If you didn't request this, please ignore this email.

        Deal Scout Team
        """

        return self.send_email(
            to_email=to_email,
            subject="Password Reset Request - Deal Scout",
            html_body=html_body,
            text_body=text_body,
        )

    def send_email_verification_email(
        self,
        to_email: str,
        username: str,
        verification_token: str,
        verification_url: Optional[str] = None,
    ) -> bool:
        """
        Send email verification email.

        Args:
            to_email: User's email address
            username: User's username
            verification_token: Email verification token
            verification_url: Optional custom verification URL

        Returns:
            True if email sent successfully, False otherwise
        """
        if verification_url is None:
            verification_url = "https://app.deal-scout.local/verify-email"

        full_verify_url = f"{verification_url}?token={verification_token}"

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Verify Your Email Address</h2>
                <p>Hi {username},</p>
                <p>Thank you for signing up! Please verify your email address by clicking the button below.</p>
                <p>
                    <a href="{full_verify_url}"
                       style="background-color: #28a745; color: white; padding: 10px 20px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email
                    </a>
                </p>
                <p>Or copy and paste this link in your browser:</p>
                <p><code>{full_verify_url}</code></p>
                <p style="color: #666; font-size: 12px;">
                    This link expires in 7 days. If you didn't create this account, please ignore this email.
                </p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">Deal Scout Team</p>
            </body>
        </html>
        """

        text_body = f"""
        Verify Your Email Address

        Hi {username},

        Thank you for signing up! Please verify your email address by visiting this link:

        {full_verify_url}

        This link expires in 7 days. If you didn't create this account, please ignore this email.

        Deal Scout Team
        """

        return self.send_email(
            to_email=to_email,
            subject="Verify Your Email Address - Deal Scout",
            html_body=html_body,
            text_body=text_body,
        )

    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """
        Send welcome email to new user.

        Args:
            to_email: User's email address
            username: User's username

        Returns:
            True if email sent successfully, False otherwise
        """
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Welcome to Deal Scout!</h2>
                <p>Hi {username},</p>
                <p>Welcome to Deal Scout! Your account has been created successfully.</p>
                <p>Start discovering amazing deals and connecting with buyers and sellers in your area.</p>
                <h3>Getting Started:</h3>
                <ul>
                    <li>Browse deals in your area</li>
                    <li>Save deals you like</li>
                    <li>Set up your notification preferences</li>
                    <li>List items for sale</li>
                </ul>
                <p>
                    <a href="https://app.deal-scout.local"
                       style="background-color: #007bff; color: white; padding: 10px 20px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Get Started
                    </a>
                </p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">Deal Scout Team</p>
            </body>
        </html>
        """

        text_body = f"""
        Welcome to Deal Scout!

        Hi {username},

        Welcome to Deal Scout! Your account has been created successfully.

        Start discovering amazing deals and connecting with buyers and sellers in your area.

        Visit https://app.deal-scout.local to get started!

        Deal Scout Team
        """

        return self.send_email(
            to_email=to_email,
            subject="Welcome to Deal Scout!",
            html_body=html_body,
            text_body=text_body,
        )

    def send_deal_alert_email(
        self,
        to_email: str,
        username: str,
        deals: list,
    ) -> bool:
        """
        Send deal alert email with matching deals.

        Args:
            to_email: User's email address
            username: User's username
            deals: List of deals to include

        Returns:
            True if email sent successfully, False otherwise
        """
        deals_html = ""
        for deal in deals:
            deals_html += f"""
            <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px;">
                <h4 style="margin-top: 0;"><a href="{deal.get('url', '#')}">{deal.get('title', 'Unknown')}</a></h4>
                <p><strong>Price:</strong> ${deal.get('price', 'N/A')}</p>
                <p><strong>Condition:</strong> {deal.get('condition', 'Unknown')}</p>
                <p><strong>Deal Score:</strong> {deal.get('deal_score', 'N/A')}</p>
                <p><strong>Category:</strong> {deal.get('category', 'Unknown')}</p>
                <p><a href="{deal.get('url', '#')}">View Listing</a></p>
            </div>
            """

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>New Deals Matching Your Preferences</h2>
                <p>Hi {username},</p>
                <p>We found {len(deals)} new deals matching your search preferences!</p>
                {deals_html}
                <p>
                    <a href="https://app.deal-scout.local/buyer/deals"
                       style="background-color: #007bff; color: white; padding: 10px 20px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        View All Deals
                    </a>
                </p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">Deal Scout Team</p>
            </body>
        </html>
        """

        return self.send_email(
            to_email=to_email,
            subject=f"New Deals Alert - {len(deals)} matches found!",
            html_body=html_body,
        )


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
