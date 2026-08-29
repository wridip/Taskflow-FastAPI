from typing import Annotated
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.token import RefreshTokenRequest, Token
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with unique email and hashed password.",
)
async def register(
    user_in: UserCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    auth_service = AuthService(session)
    user = await auth_service.register(user_in)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="User login (JSON)",
    description="Authenticate with email and password to receive JWT access and refresh tokens.",
)
async def login_json(
    credentials: UserLogin,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    auth_service = AuthService(session)
    return await auth_service.authenticate(credentials.email, credentials.password)


@router.post(
    "/login/access-token",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="OAuth2 Password Flow Login (Swagger compatible)",
    description="Authenticate using form-data for Swagger UI 'Authorize' button.",
)
async def login_oauth2(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    auth_service = AuthService(session)
    return await auth_service.authenticate(form_data.username, form_data.password)


@router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token and refresh token pair.",
)
async def refresh_token(
    req: RefreshTokenRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    auth_service = AuthService(session)
    return await auth_service.refresh_access_token(req.refresh_token)
