from fastapi import FastAPI
from database import engine, Base
from contextlib import asynccontextmanager
from routers import task, user

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
app.include_router(task.router, prefix="/api/items", tags=["tasks"])
app.include_router(user.router, prefix="/api/users", tags=["users"])

@app.get("/health_check")
async def root():
    return {"status": "Healthy"}






