import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple

import jwt
from redis.asyncio import Redis

from ..utils import setup_logger
from .config import (
    JWT_ALGORITHM,
    JWT_SECRET,
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
    VERIFICATION_TOKEN_EXPIRE_MINUTES,
)

logger = setup_logger()


async def generate_verification_token(user_id: int, username: str, redis: Redis) -> str:
    """
    Generates a verification token for account activation

    Args:
        user_id: The user's ID
        username: The user's username (email)
        redis: Redis connection

    Returns:
        JWT token for email verification
    """
    # Generate JWT token
    token_jti = secrets.token_hex(16)  # Add unique ID to prevent token reuse
    payload = {
        "sub": str(user_id),
        "username": username,
        "type": "verification",
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=VERIFICATION_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
        "jti": token_jti,
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Store token in Redis with expiry for additional security
    await redis.set(
        f"verification_token:{token_jti}",
        str(user_id),
        ex=VERIFICATION_TOKEN_EXPIRE_MINUTES * 60,
    )

    logger.info(f"Generated verification token for user {user_id}")
    return token


async def generate_password_reset_token(
    user_id: int, username: str, redis: Redis
) -> str:
    """
    Generates a token for password reset

    Args:
        user_id: The user's ID
        username: The user's username (email)
        redis: Redis connection

    Returns:
        JWT token for password reset
    """
    # Generate JWT token
    token_jti = secrets.token_hex(16)  # Add unique ID to prevent token reuse
    payload = {
        "sub": str(user_id),
        "username": username,
        "type": "password_reset",
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
        "jti": token_jti,
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Store token in Redis with expiry for additional security
    await redis.set(
        f"password_reset_token:{token_jti}",
        str(user_id),
        ex=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES * 60,
    )

    logger.info(f"Generated password reset token for user {user_id}")
    return token


async def verify_token(token: str, token_type: str, redis: Redis) -> Tuple[bool, Dict]:
    """
    Verifies a token and returns user information if valid

    Args:
        token: The JWT token
        token_type: Either "verification" or "password_reset"
        redis: Redis connection

    Returns:
        Tuple of (is_valid, payload)
    """
    try:
        # Decode the token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Check token type
        if payload.get("type") != token_type:
            logger.warning(
                f"Invalid token type: expected {token_type}, got {payload.get('type')}"
            )
            return False, {}

        # Check if token is in Redis (hasn't been used)
        token_key = f"{token_type}_token:{payload['jti']}"
        stored_user_id = await redis.get(token_key)

        if not stored_user_id or stored_user_id.decode() != payload["sub"]:
            logger.warning(
                "Token validation failed: token not found in Redis or user_id mismatch"
            )
            return False, {}

        # If verification successful, invalidate token to prevent reuse
        await redis.delete(token_key)

        logger.info(
            f"Successfully verified {token_type} token for user {payload['sub']}"
        )
        return True, payload

    except jwt.PyJWTError as e:
        logger.error(f"JWT token verification error: {str(e)}")
        return False, {}
