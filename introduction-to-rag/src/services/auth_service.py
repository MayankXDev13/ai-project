from sqlmodel import Session, select
from src.models.users import User
from src.lib.security import hash_password, verify_password, create_access_token

class AuthError(Exception):
    pass

def register_user(session: Session, email: str, password: str) -> User:
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise AuthError("Email already registered")
    user = User(email=email, hash_password=hash_password(password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def authenticate_user(session: Session, email: str, password: str) -> str:
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.hash_password):
        raise AuthError("Invalid email or password")
    if user.deleted_at is not None:
        raise AuthError("Account has been deactivated")
    return create_access_token({"sub": user.id})
