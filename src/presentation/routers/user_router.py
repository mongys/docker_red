# src/presentation/routers/user_router.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordRequestForm  # Добавлен импорт
from src.application.services.auth.auth_service import AuthService
from src.presentation.dependencies import get_auth_service, get_current_user, get_refresh_token, get_token_tools
from src.presentation.schemas import UserCreateModel, UserResponseModel
from src.domain.entities import User
from src.domain.exceptions import UserAlreadyExistsException, AuthenticationException  # Добавлены импорты
from src.application.services.token.token_tools import TokenTools
from src.application.services.token.refresh_token import RefreshToken
from typing import Dict
from datetime import datetime, timedelta
from config.config import settings

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    # dependencies=[]  # Можно убрать, если не добавляются глобальные зависимости
)

logger = logging.getLogger(__name__)


@router.post(
    "/signup",
    response_model=Dict[str, str],
    summary="Register a new user",
    description="Creates a new user in the system. Returns a message about successful registration.",
    responses={
        200: {"description": "User successfully created."},
        400: {"description": "A user with this username already exists."},
    }
)
async def signup(
    user_data: UserCreateModel,
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, str]:
    """
    Registers a new user with the provided username and password.

    Args:
        user_data (UserCreateModel): The data containing the username and password for the new user.
        auth_service (AuthService): The authentication service dependency.

    Returns:
        Dict[str, str]: A dictionary containing a success message.

    Raises:
        HTTPException: If a user with the provided username already exists.
    """
    try:
        await auth_service.create_user(user_data.username, user_data.password)
        return {"message": "User created successfully"}
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/token",
    response_model=Dict[str, str],
    summary="Authenticate user and set tokens in cookies",
    description="Authenticates a user and sets access and refresh tokens in HttpOnly cookies.",
)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, str]:
    logger.info(f"Attempting login for username: {form_data.username}")
    try:
        user = await auth_service.authenticate_user(form_data.username, form_data.password)
        logger.info(f"User authenticated: {user.username}")
        access_token = auth_service.create_token(
            data={"sub": user.username},
            token_type="access",
            expires_delta=timedelta(minutes=15)
        )
        logger.info(f"Access token created for user: {user.username}")

        refresh_token = auth_service.create_token(
            data={"sub": user.username},
            token_type="refresh",
            expires_delta=timedelta(days=7)
        )
        logger.info(f"Refresh token created for user: {user.username}")

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True, 
            samesite="lax",
            max_age=settings.access_token_expire_minutes * 60
        )
        logger.info("Access token set in cookies")

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  
            samesite="lax",
            max_age=settings.refresh_token_expire_days * 24 * 60 * 60
        )
        logger.info("Refresh token set in cookies")

        return {"message": "Login successful"}
    except AuthenticationException:
        logger.warning("Authentication failed for user")
        raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/tokens/current",
    response_model=Dict[str, str],
    summary="Get current tokens' expiration info",
    description="Returns the expiration times for the current access and refresh tokens for the authenticated user.",
    responses={
        200: {"description": "Tokens expiration information retrieved successfully."},
        401: {"description": "Unauthorized access."},
    }
)
async def get_current_tokens(
    request: Request,
    current_user: User = Depends(get_current_user),
    token_tools: TokenTools = Depends(get_token_tools)
) -> Dict[str, str]:
    """
    Retrieves the expiration times for the current access and refresh tokens for the authenticated user.

    Args:
        request (Request): The HTTP request object containing cookies.
        current_user (User): The currently authenticated user, provided by the dependency.
        token_tools (TokenTools): The service for handling token operations.

    Returns:
        Dict[str, str]: A dictionary containing expiration times of access and refresh tokens.
    """
    try:
        # Извлекаем токены из куки
        access_token = request.cookies.get("access_token")
        refresh_token = request.cookies.get("refresh_token")

        if not access_token:
            raise HTTPException(status_code=401, detail="Access token is missing.")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token is missing.")

        # Декодируем токены для получения времени истечения
        access_payload = token_tools.validate_token(access_token)
        refresh_payload = token_tools.validate_token(refresh_token)

        return {
            "access_token_expiry": datetime.utcfromtimestamp(access_payload["exp"]).isoformat(),
            "refresh_token_expiry": datetime.utcfromtimestamp(refresh_payload["exp"]).isoformat(),
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving tokens: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve tokens and expiration info.")


@router.post(
    "/logout",
    response_model=Dict[str, str],
    summary="Logout user",
    description="Logs out the user by clearing the tokens from cookies.",
    responses={
        200: {"description": "Logged out successfully."},
    }
)
async def logout(
    response: Response
) -> Dict[str, str]:
    """
    Logs out the user by clearing the tokens from cookies.

    Args:
        response (Response): The HTTP response object to delete cookies.

    Returns:
        Dict[str, str]: A dictionary containing a success message.
    """
    # Удаляем куки
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    logger.info("User logged out and tokens cleared from cookies")

    return {"message": "Logged out successfully"}


@router.post(
    "/refresh_token",
    response_model=Dict[str, str],
    summary="Refresh access token",
    description="Refreshes an expired access token using the refresh token stored in the HttpOnly cookie.",
)
async def refresh_access_token( 
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    refresh_token: RefreshToken = Depends(get_refresh_token)
) -> Dict[str, str]:
    """
    Refreshes an expired access token using the refresh token stored in the HttpOnly cookie.

    Args:
        request (Request): The HTTP request object containing cookies.
        response (Response): The HTTP response object to set cookies.
        auth_service (AuthService): The authentication service dependency.

    Returns:
        Dict[str, str]: A dictionary containing a success message.
    """
    # Получаем refresh_token из куки
    refresh_token_value = request.cookies.get("refresh_token")
    logger.info("Attempting to refresh access token")

    if not refresh_token_value:
        logger.warning("Unauthorized")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        new_access_token = await auth_service.refresh_access_token(refresh_token_value)
        
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,  
            samesite="lax",
            max_age=settings.access_token_expire_minutes * 60
        )
        logger.info("Access token refreshed and set in cookies")
        
        return {"message": "Access token refreshed successfully"}
    except HTTPException as e:
        logger.warning(f"HTTPException during refresh token: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during refresh token: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/users/me",
    response_model=UserResponseModel,
    summary="Get current user information",
    description="Returns information about the currently authenticated user.",
)
async def read_users_me(
    current_user: User = Depends(get_current_user)
) -> UserResponseModel:
    """
    Retrieves information about the currently authenticated user.

    Args:
        current_user (User): The currently authenticated user, provided by the dependency.

    Returns:
        UserResponseModel: A Pydantic model containing the user's information.
    """
    return UserResponseModel(username=current_user.username)
