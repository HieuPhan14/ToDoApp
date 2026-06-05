from fastapi import APIRouter, HTTPException, Path, status, Query, Depends
from database import get_db
from models.user import User
from schemas import UserCreate, UserResponse
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("", response_model=list[UserResponse])
async def get_all_users(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(User)
    )
    users = result.scalars().all()

    return users

@router.get("/{user_id}", response_model=UserResponse)
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

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    pass

    # record = User(
    #     username= user.username,
    #     email= user.email,
    #     password= user.password
    # )
    # db.add(record)
    # await db.commit()
    # await db.refresh(record)

    # return record

