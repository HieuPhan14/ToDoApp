from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///./todo.db"

engine = create_async_engine(DATABASE_URL)

class Base(DeclarativeBase):
    pass

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db


