import logging
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordRequestForm  
from src.application.services.auth.auth_service import AuthService
from src.presentation.dependencies import (
    get_auth_service,
    get_current_user,
    get_refresh_token,
    get_TokenCreator,
    get_token_validator)
from src.presentation.schemas import UserCreateModel, UserResponseModel
from src.domain.entities import User
from src.domain.exceptions import UserAlreadyExistsException, AuthenticationException  
from src.application.services.token.token_creator import TokenCreator
from src.application.services.token.token_refresher import RefreshToken
from src.application.services.token.token_validator import TokenValidator
from typing import Dict
from datetime import datetime, timedelta
from config.config import settings

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
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
    "/signup",
    response_model=Dict[str, str],
    summary="Authenticate user and set tokens in cookies",
    description="Authenticates a user and sets access and refresh tokens in HttpOnly cookies.",
)
async def signup(
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
        new_access_token = await auth_service.refresh_token(refresh_token_value)

        
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
