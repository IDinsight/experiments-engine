from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.requests import Request
from fastapi.security import OAuth2PasswordRequestForm
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_async_session, get_redis
from ..email import EmailService
from ..users.models import (
    UserNotFoundError,
    get_user_by_username,
    update_user_password,
    update_user_verification_status,
)
from ..users.schemas import (
    EmailVerificationRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
)
from ..utils import setup_logger
from .config import NEXT_PUBLIC_GOOGLE_LOGIN_CLIENT_ID
from .dependencies import (
    authenticate_credentials,
    authenticate_or_create_google_user,
    create_access_token,
)
from .schemas import AuthenticationDetails, GoogleLoginData
from .utils import (
    generate_password_reset_token,
    generate_verification_token,
    verify_token,
)

TAG_METADATA = {
    "name": "Authentication",
    "description": "_Requires user login._ Endpoints for authenticating user logins.",
}

router = APIRouter(tags=[TAG_METADATA["name"]])

email_service = EmailService()
logger = setup_logger()


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    asession: AsyncSession = Depends(get_async_session),
) -> AuthenticationDetails:
    """
    Login route for users to authenticate and receive a JWT token.
    """
    user = await authenticate_credentials(
        username=form_data.username,
        password=form_data.password,
        asession=asession,
    )
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )

    return AuthenticationDetails(
        access_token=create_access_token(user.username),
        api_key_first_characters=user.api_key_first_characters,
        token_type="bearer",
        access_level=user.access_level,
        username=user.username,
        is_verified=user.is_verified,
    )


@router.post("/login-google")
async def login_google(
    request: Request,
    login_data: GoogleLoginData,
    asession: AsyncSession = Depends(get_async_session),
) -> AuthenticationDetails:
    """
    Verify google token, check if user exists. If user does not exist, create user
    Return JWT token for user. Google users are automatically verified.
    """

    try:
        idinfo = id_token.verify_oauth2_token(
            login_data.credential,
            google_requests.Request(),
            NEXT_PUBLIC_GOOGLE_LOGIN_CLIENT_ID,
        )
        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Wrong issuer.")

    except ValueError as e:
        logger.error(
            f"Invalid token: {e}, client_id: {NEXT_PUBLIC_GOOGLE_LOGIN_CLIENT_ID}"
        )
        raise HTTPException(status_code=401, detail="Invalid token") from e

    user = await authenticate_or_create_google_user(
        request=request,
        google_email=idinfo["email"],
        asession=asession,
        first_name=idinfo["given_name"],
        last_name=idinfo["family_name"],
    )
    if not user:
        raise HTTPException(
            status_code=500,
            detail="Unable to create new user",
        )

    return AuthenticationDetails(
        access_token=create_access_token(user.username),
        api_key_first_characters=user.api_key_first_characters,
        token_type="bearer",
        access_level=user.access_level,
        username=user.username,
        is_verified=user.is_verified,
    )


@router.post("/request-password-reset", response_model=MessageResponse)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    asession: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """
    Request a password reset email
    """
    response_msg = (
        "If an account with this email exists, a password reset link has been sent."
    )

    try:
        logger.info(f"Generated password reset token for user {reset_request.username}")
        user = await get_user_by_username(reset_request.username, asession)

        logger.info(f"User found: {user.username}")
        if not user:
            return MessageResponse(message=response_msg)

        token = await generate_password_reset_token(user.user_id, user.username, redis)
        background_tasks.add_task(
            email_service.send_password_reset_email, user.username, user.username, token
        )

        return MessageResponse(message=response_msg)
    except UserNotFoundError:
        logger.warning(f"User not found: {reset_request.username}")
        return MessageResponse(message=response_msg)
    except Exception as e:
        logger.exception("An error occurred processing your request")
        raise HTTPException(
            status_code=500, detail="An error occurred processing your request"
        ) from e


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    asession: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """
    Reset a user's password with the provided token
    """
    is_valid, payload = await verify_token(reset_data.token, "password_reset", redis)

    if not is_valid or "username" not in payload:
        raise HTTPException(
            status_code=400, detail="Invalid or expired password reset token"
        )

    try:
        user = await get_user_by_username(payload["username"], asession)
        asession.add(user)

        await update_user_password(user, reset_data.new_password, asession)

        return MessageResponse(message="Your password has been reset successfully")
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail="User not found") from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="An error occurred while resetting your password"
        ) from e


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verification_data: EmailVerificationRequest,
    asession: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """
    Verify a user's email with the provided token
    """
    is_valid, payload = await verify_token(
        verification_data.token, "verification", redis
    )

    if not is_valid or "username" not in payload:
        raise HTTPException(
            status_code=400, detail="Invalid or expired verification token"
        )

    try:
        user = await get_user_by_username(payload["username"], asession)

        asession.add(user)
        await update_user_verification_status(user, True, asession)

        return MessageResponse(message="Your email has been verified successfully")
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail="User not found") from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="An error occurred while verifying your email"
        ) from e


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    reset_request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    asession: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """
    Resend verification email
    """
    response_msg = (
        "If an account with this email exists, a password reset link has been sent."
    )

    try:
        user = await get_user_by_username(reset_request.username, asession)

        if not user:
            return MessageResponse(message=response_msg)

        if user.is_verified:
            return MessageResponse(message="Your account is already verified")

        token = await generate_verification_token(user.user_id, user.username, redis)

        background_tasks.add_task(
            email_service.send_verification_email, user.username, user.username, token
        )

        return MessageResponse(message=response_msg)
    except UserNotFoundError:
        return MessageResponse(message=response_msg)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="An error occurred processing your request"
        ) from e
