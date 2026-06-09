from __future__ import annotations
from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)

    tasks: Mapped[list["Task"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    image_file: Mapped[str | None] = mapped_column(String(200), default=None)

    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"