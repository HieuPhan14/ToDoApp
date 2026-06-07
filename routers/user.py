from fastapi import APIRouter, HTTPException, Path, status, Query, Depends
from fastapi.security import OAuth2PasswordRequestForm
from database import get_db
from models.user import User
from schemas import UserCreate, UserPrivate, Token, UserPublic
from typing import Annotated
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from auth import CurrentUser, get_password_hash, verify_password, DUMMY_HASH, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta

router = APIRouter()

@router.post("/token", response_model=Token)
async def generate_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    result = await db.execute(
        select(User).
        where(func.lower(User.email) == form_data.username.lower())
    )
    user = result.scalars().first()

    if not user:
        verify_password(form_data.password, DUMMY_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    pass_check = verify_password(form_data.password, user.hashed_password)
    if not pass_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expire = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        {"sub": str(user.id)}, 
        access_token_expire
    )

    return Token(access_token=token, token_type="bearer")

@router.get("/me", response_model=UserPrivate)
async def get_current_user(
    current_user: CurrentUser
):
    return current_user
    

@router.get("", response_model=list[UserPublic])
async def get_all_users(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(User)
    )
    users = result.scalars().all()

    return users

@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(User).
        where(User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This person ain't real"
        )
    
    return user

@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(User).
        where(func.lower(User.username) == user.username.lower())
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username exists"
        )
    
    result = await db.execute(
        select(User).
        where(func.lower(User.email) == user.email.lower())
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email exists"
        )
    
    new_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        email=user.email.lower()
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user
    
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    user_id: int
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this person"
        )
    
    result = await db.execute(
        select(User).
        where(User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This person ain't real to delete"
        )
    
    await db.delete(user)
    await db.commit()

    

