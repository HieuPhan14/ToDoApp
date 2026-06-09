from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
import jwt
from pwdlib import PasswordHash
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from database import get_db
from models.user import User
from sqlalchemy import select
from config import settings

password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("dummypassword")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/token")

def verify_password(plained_password, hashed_password):
    return password_hash.verify(plained_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)

def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)

def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

async def get_user(
    db: AsyncSession,
    user_id: int
) -> User | None:
    result = await db.execute(
        select(User).
        where(User.id == user_id) 
    )
    return result.scalars().first()


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key.get_secret_value(), algorithm=settings.algorithm)
    return encoded_jwt

def verify_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=[settings.algorithm])
    except InvalidTokenError:
        return None
    else: 
        return payload.get("sub") 

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
    ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
   
    user_id = verify_access_token(token)
    if user_id is None:
        raise credentials_exception
    
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise credentials_exception

    user = await get_user(db, user_id_int)
    if user is None:
        raise credentials_exception
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

