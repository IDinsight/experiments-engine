from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException

from .config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    FRONTEND_URL,
    SES_REGION,
    SES_SENDER_EMAIL,
)
from .utils import setup_logger

logger = setup_logger()


class EmailService:
    """Service to send emails via AWS SES"""

    def __init__(
        self,
        aws_region: Optional[str] = None,
        sender_email: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ) -> None:
        """Initialize the email service with AWS credentials"""
        self.aws_region = aws_region or SES_REGION
        self.sender_email = sender_email or SES_SENDER_EMAIL

        session_kwargs: Dict[str, Any] = {"region_name": self.aws_region}

        aws_access_key = aws_access_key_id or AWS_ACCESS_KEY_ID
        aws_secret_key = aws_secret_access_key or AWS_SECRET_ACCESS_KEY

        if aws_access_key and aws_secret_key:
            session_kwargs.update(
                {
                    "aws_access_key_id": aws_access_key,
                    "aws_secret_access_key": aws_secret_key,
                }
            )

        self.client = boto3.client("ses", **session_kwargs)

    async def send_verification_email(
        self, email: str, username: str, token: str
    ) -> Dict[str, Any]:
        """
        Send account verification email
        """
        verification_url = f"{FRONTEND_URL}/verify?token={token}"

        subject = "Verify Your Account"
        html_body = f"""
        <html>
        <head></head>
        <body>
            <h1>Account Verification</h1>
            <p>Hello {username},</p>
            <p>Thank you for signing up. Please click the link below to verify
            your account:</p>
            <p><a href="{verification_url}">Verify My Account</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you did not create this account, please ignore this email.</p>
        </body>
        </html>
        """
        text_body = f"""
        Account Verification

        Hello {username},

        Thank you for signing up. Please use the link below to verify your account:

        {verification_url}

        This link will expire in 24 hours.

        If you did not create this account, please ignore this email.
        """

        return await self._send_email(email, subject, html_body, text_body)

    async def send_password_reset_email(
        self, email: str, username: str, token: str
    ) -> Dict[str, Any]:
        """
        Send password reset email
        """
        reset_url = f"{FRONTEND_URL}/reset-password?token={token}"

        subject = "Password Reset Request"
        html_body = f"""
        <html>
        <head></head>
        <body>
            <h1>Password Reset</h1>
            <p>Hello {username},</p>
            <p>We received a request to reset your password. Please click the link below
            to set a new password:</p>
            <p><a href="{reset_url}">Reset My Password</a></p>
            <p>This link will expire in 30 minutes.</p>
            <p>If you did not request a password reset, please ignore this email.</p>
        </body>
        </html>
        """
        text_body = f"""
        Password Reset

        Hello {username},

        We received a request to reset your password. Please use the link below
        to set a new password:

        {reset_url}

        This link will expire in 30 minutes.

        If you did not request a password reset, please ignore this email.
        """

        return await self._send_email(email, subject, html_body, text_body)

    async def _send_email(
        self, recipient: str, subject: str, html_body: str, text_body: str
    ) -> Dict[str, Any]:
        """
        Send an email using AWS SES
        """

        try:
            response = self.client.send_email(
                Source=self.sender_email,
                Destination={
                    "ToAddresses": [recipient],
                },
                Message={
                    "Subject": {
                        "Data": subject,
                    },
                    "Body": {
                        "Text": {
                            "Data": text_body,
                        },
                        "Html": {
                            "Data": html_body,
                        },
                    },
                },
            )
            logger.info(
                f"Email sent to {recipient}! Message ID: {response.get('MessageId')}"
            )
            return response
        except ClientError as e:
            error_message = f"Error sending email to {recipient}: {e}"
            logger.error(error_message)
            raise HTTPException(
                status_code=500, detail=f"Failed to send email: {str(e)}"
            ) from e
