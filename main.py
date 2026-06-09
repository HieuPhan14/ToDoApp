from fastapi import FastAPI
from database import engine
from contextlib import asynccontextmanager
from routers import task, user
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Shut down
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(task.router, prefix="/api/items", tags=["tasks"])
app.include_router(user.router, prefix="/api/users", tags=["users"])

@app.get("/health_check")
async def root():
    return {"status": "Healthy"}






