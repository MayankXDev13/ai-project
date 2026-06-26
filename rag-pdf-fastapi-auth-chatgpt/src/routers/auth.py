from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from src.db.database import get_session
from src.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from src.services.auth_service import register_user, authenticate_user, AuthError
from src.utils.dependencies import get_current_user
from src.models.users import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, session: Session = Depends(get_session)):
    try:
        user = await register_user(session, body.email, body.password)
        return UserResponse(id=user.id, email=user.email)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: Session = Depends(get_session)):
    try:
        token = await authenticate_user(session, body.email, body.password)
        return TokenResponse(access_token=token)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse(id=user.id, email=user.email)
