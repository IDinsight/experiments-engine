"""This module contains utility functions for the backend application."""

# pylint: disable=global-statement
import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from logging import Logger
from uuid import uuid4

from redis import asyncio as aioredis

from .config import (
    LOG_LEVEL,
)

# To make 32-byte API keys (results in 43 characters)
SECRET_KEY_N_BYTES = 32


def generate_key() -> str:
    """
    Generate API key (default 32 byte = 43 characters)
    """

    return secrets.token_urlsafe(SECRET_KEY_N_BYTES)


def get_key_hash(key: str) -> str:
    """Hashes the api key using SHA256."""
    return hashlib.sha256(key.encode()).hexdigest()


def get_password_salted_hash(key: str) -> str:
    """Hashes the password using SHA256 with a salt."""
    salt = os.urandom(16)
    key_salt_combo = salt + key.encode()
    hash_obj = hashlib.sha256(key_salt_combo)
    return salt.hex() + hash_obj.hexdigest()


def verify_password_salted_hash(key: str, stored_hash: str) -> bool:
    """Verifies if the api key matches the hash."""
    salt = bytes.fromhex(stored_hash[:32])
    original_hash = stored_hash[32:]
    key_salt_combo = salt + key.encode()
    hash_obj = hashlib.sha256(key_salt_combo)

    return hash_obj.hexdigest() == original_hash


def get_random_string(size: int) -> str:
    """Generate a random string of fixed length."""
    import random
    import string

    return "".join(random.choices(string.ascii_letters + string.digits, k=size))


def get_log_level_from_str(log_level_str: str = LOG_LEVEL) -> int:
    """
    Get log level from string
    """
    log_level_dict = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }

    return log_level_dict.get(log_level_str.upper(), logging.INFO)


def generate_secret_key() -> str:
    """
    Generate a secret key for the user query
    """
    return uuid4().hex


def setup_logger(
    name: str = __name__, log_level: int = get_log_level_from_str()
) -> Logger:
    """
    Setup logger for the application
    """
    logger = logging.getLogger(name)

    # If the logger already has handlers,
    # assume it was already configured and return it.
    if logger.handlers:
        return logger

    logger.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s %(filename)20s%(lineno)4s : %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
    )

    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def encode_api_limit(api_limit: int | None) -> int | str:
    """
    Encode the api limit for redis
    """

    return int(api_limit) if api_limit is not None else "None"


async def update_api_limits(
    redis: aioredis.Redis, username: str, api_daily_quota: int | None
) -> None:
    """
    Update the api limits for user in Redis
    """
    now = datetime.now(timezone.utc)
    next_midnight = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    key = f"remaining-calls:{username}"
    expire_at = int(next_midnight.timestamp())
    await redis.set(key, encode_api_limit(api_daily_quota))
    if api_daily_quota is not None:
        await redis.expireat(key, expire_at)
