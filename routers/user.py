from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    UploadFile,
    status,
    Depends,
)
from fastapi.concurrency import run_in_threadpool
from fastapi.security import OAuth2PasswordRequestForm
from database import get_db
from email_utils import send_password_reset_email
from image_utils import delete_profile_image, process_profile_image
from PIL import UnidentifiedImageError
from models.user import User
from schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserCreate,
    UserPrivate,
    Token,
    UserPublic,
    UserUpdate,
)
from typing import Annotated
from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from auth import (
    CurrentUser,
    generate_reset_token,
    get_password_hash,
    hash_reset_token,
    verify_password,
    DUMMY_HASH,
    create_access_token,
)
from datetime import UTC, datetime, timedelta
from config import settings
from models.password_reset import PasswordResetToken

router = APIRouter()


@router.post("/token", response_model=Token)
async def generate_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    result = await db.execute(
        select(User).where(func.lower(User.email) == form_data.username.lower())
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

    access_token_expire = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token({"sub": str(user.id)}, access_token_expire)

    return Token(access_token=token, token_type="bearer")


@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    return current_user


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(User).where(func.lower(User.email) == request_data.email.lower())
    )
    user = result.scalars().first()

    if user:
        await db.execute(
            delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
        )

        token = generate_reset_token()
        token_hash = hash_reset_token(token)
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.reset_token_expire_minutes
        )

        reset_token = PasswordResetToken(
            user_id=user.id, token_hash=token_hash, expires_at=expires_at
        )

        db.add(reset_token)
        await db.commit()

        background_tasks.add_task(
            send_password_reset_email,
            to_email=user.email,
            username=user.username,
            token=token,
        )

    return {
        "message": "If an account exists with this email, you will receive password reset instructions."
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request_data: ResetPasswordRequest, db: Annotated[AsyncSession, Depends(get_db)]
):
    token_hash = hash_reset_token(request_data.token)

    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    reset_token = result.scalars().first()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    
    if reset_token.expires_at < datetime.now(UTC):
        await db.delete(reset_token)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    result = await db.execute(
        select(User).
        where(User.id == reset_token.user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user.hashed_password = get_password_hash(request_data.new_password)

    await db.execute(
        delete(PasswordResetToken).
        where(PasswordResetToken.user_id == user.id)
    )

    await db.commit()
    return {
        "message": "Password reset successfully."
    }

@router.patch("/me/password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.hashed_password = get_password_hash(password_data.new_password)

    await db.execute(
        delete(PasswordResetToken).
        where(PasswordResetToken.user_id == current_user.id)
    )
    await db.commit()
    return {"message": "Password changed successfully"}

@router.get("", response_model=list[UserPublic])
async def get_all_users(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User))
    users = result.scalars().all()

    return users


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

    result = await db.execute(
        select(User).where(func.lower(User.email) == user.email.lower())
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    new_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        email=user.email.lower(),
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    user_id: int,
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    old_filename = user.image_file

    await db.delete(user)
    await db.commit()

    if old_filename:
        delete_profile_image(old_filename)


@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(
    update_info: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    user_id: int,
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if (
        update_info.email is not None
        and update_info.email.lower() != current_user.email.lower()
    ):
        result = await db.execute(
            select(User).where(func.lower(User.email) == update_info.email.lower())
        )

        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    if (
        update_info.username is not None
        and update_info.username != current_user.username
    ):
        result = await db.execute(
            select(User).where(User.username == update_info.username)
        )

        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

    updated_info = update_info.model_dump(exclude_unset=True)

    for key, value in updated_info.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)

    return user


@router.patch("/{user_id}/picture", response_model=UserPrivate)
async def upload_profile_picture(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    file: UploadFile,
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's picture",
        )

    content = await file.read()

    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {settings.max_upload_size_bytes // (1024*1024)} MB",
        )

    try:
        new_filename = await run_in_threadpool(process_profile_image, content)
    except UnidentifiedImageError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Please upload a valid image (JPEG, PNG, GIF, WebP).",
        ) from err

    old_filename = current_user.image_file

    current_user.image_file = new_filename
    await db.commit()
    await db.refresh(current_user)

    if old_filename:
        delete_profile_image(old_filename)

    return current_user


@router.delete("/{user_id}/picture", response_model=UserPrivate)
async def delete_user_picture(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user's picture",
        )

    old_filename = current_user.image_file

    if old_filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile picture to delete",
        )

    current_user.image_file = None
    await db.commit()
    await db.refresh(current_user)

    delete_profile_image(old_filename)

    return current_user
