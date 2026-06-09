import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy import delete, select, update

from database import AsyncSessionLocal, engine
from main import app
from models.task import Task
from models.user import User

POPULATE_IMAGES_DIR = Path("media/profile_pics")

USERS = [
    {
        "username": "AlphaUser",
        "email": "alpha@example.com",
        "password": "Password1!",
        "image": "4dogs.jpg",
    },
    {
        "username": "BetaUser",
        "email": "beta@example.com",
        "password": "Password2!",
        "image": "singledog.jpg",
    },
    {
        "username": "GammaUser",
        "email": "gamma@example.com",
        "password": "Password3!",
        "image": "catbush.jpg",
    },
    {
        "username": "DeltaUser",
        "email": "delta@example.com",
        "password": "Password4!",
        "image": "dogcode.jpg",
    },
    {
        "username": "EpsilonUser",
        "email": "epsilon@example.com",
        "password": "Password5!",
        # No image - uses default
    },
    {
        "username": "ZetaUser",
        "email": "zeta@example.com",
        "password": "Password6!",
        # No image - uses default
    },
]

TASKS = [
    {
        "title": "Set up FastAPI project",
        "content": "Initialize the project structure, install dependencies, and configure the database.",
        "status": "completed",
        "due_date": None,
    },
    {
        "title": "Design database schema",
        "content": "Plan the User and Task models, define relationships and constraints.",
        "status": "completed",
        "due_date": None,
    },
    {
        "title": "Implement user registration",
        "content": "Build the POST /api/users route with duplicate checks and password hashing.",
        "status": "completed",
        "due_date": None,
    },
    {
        "title": "Implement JWT authentication",
        "content": "Create token generation and verification, wire up the /token route.",
        "status": "completed",
        "due_date": None,
    },
    {
        "title": "Add profile picture upload",
        "content": "Integrate Pillow for image processing, save files to disk, store filename in DB.",
        "status": "completed",
        "due_date": None,
    },
    {
        "title": "Write populate_db script",
        "content": "Seed the database with realistic users and tasks for development and testing.",
        "status": "completed",
        "due_date": None,
    },
    {
        "title": "Add task filtering by status",
        "content": "Implement GET /api/items/status/{status_type} with proper error handling.",
        "status": "completed",
        "due_date": None,
    },
    {
        "title": "Write unit tests for auth",
        "content": "Cover token creation, verification, and the get_current_user dependency.",
        "status": "in_progress",
        "due_date": None,
    },
    {
        "title": "Write integration tests for task routes",
        "content": "Test all CRUD operations including ownership checks and 403 responses.",
        "status": "in_progress",
        "due_date": None,
    },
    {
        "title": "Add pagination to task listing",
        "content": "Implement cursor-based or limit/offset pagination on GET /api/items.",
        "status": "in_progress",
        "due_date": None,
    },
    {
        "title": "Move secrets to environment variables",
        "content": "Use pydantic-settings to load SECRET_KEY and other config from .env file.",
        "status": "completed",
        "due_date": None,
    },
    {
        "title": "Set up CI pipeline",
        "content": "Configure GitHub Actions to run tests on every pull request.",
        "status": "pending",
        "due_date": None,
    },
    {
        "title": "Deploy to production server",
        "content": "Provision a VPS, configure nginx as a reverse proxy, and run uvicorn.",
        "status": "pending",
        "due_date": None,
    },
    {
        "title": "Add rate limiting",
        "content": "Protect the API from abuse by limiting requests per IP per minute.",
        "status": "pending",
        "due_date": None,
    },
    {
        "title": "Implement password reset via email",
        "content": "Generate a reset token, send it by email, and allow the user to set a new password.",
        "status": "pending",
        "due_date": None,
    },
    {
        "title": "Add task due date reminders",
        "content": "Send email notifications when a task due date is approaching.",
        "status": "pending",
        "due_date": None,
    },
    {
        "title": "Refactor error handling",
        "content": "Centralize exception handling and standardize error response format.",
        "status": "pending",
        "due_date": None,
    },
    {
        "title": "Add task search",
        "content": "Allow users to search tasks by title or content using a query parameter.",
        "status": "pending",
        "due_date": None,
    },
    {
        "title": "Implement task sorting",
        "content": "Support sorting by due_date, created_at, and status on the listing endpoint.",
        "status": "pending",
        "due_date": None,
    },
    {
        "title": "Optimize database queries",
        "content": "Add indexes and review slow queries using SQLAlchemy's query logging.",
        "status": "pending",
        "due_date": None,
    },
    {
        "title": "Document the API",
        "content": "Add descriptions and examples to all routes so Swagger UI is fully self-explanatory.",
        "status": "in_progress",
        "due_date": None,
    },
    {
        "title": "Set up database backups",
        "content": "Schedule daily automated backups of the SQLite file to cloud storage.",
        "status": "pending",
        "due_date": None,
    },
    {
        "title": "Add CORS configuration",
        "content": "Configure allowed origins for the frontend domain in production.",
        "status": "completed",
        "due_date": None,
    },
    {
        "title": "Review dependency versions",
        "content": "Run pip list --outdated and update packages safely without breaking changes.",
        "status": "pending",
        "due_date": None,
    },
    {
        "title": "Add health check endpoint",
        "content": "Return 200 with DB connectivity status so load balancers can verify uptime.",
        "status": "completed",
        "due_date": None,
    },
    {
        "title": "Switch to PostgreSQL",
        "content": "Migrate from SQLite to PostgreSQL for production-grade concurrency support.",
        "status": "pending",
        "due_date": None,
    },
    {
        "title": "Containerize with Docker",
        "content": "Write a Dockerfile and docker-compose.yml for consistent dev and prod environments.",
        "status": "pending",
        "due_date": None,
    },
    {
        "title": "Add logging",
        "content": "Set up structured logging with log levels and request tracing.",
        "status": "pending",
        "due_date": None,
    },
    {
        "title": "Implement soft delete for tasks",
        "content": "Add a deleted_at column so tasks can be recovered instead of permanently removed.",
        "status": "pending",
        "due_date": None,
    },
    {
        "title": "Build a frontend",
        "content": "Create a simple React or Vue frontend to consume the API.",
        "status": "pending",
        "due_date": None,
    },
]


async def clear_existing_data() -> None:
    async with engine.begin() as conn:
        from database import Base
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        await db.execute(delete(Task))
        await db.execute(delete(User))
        await db.commit()
    print("Cleared existing data")


async def update_task_dates() -> None:
    now = datetime.now(UTC)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Task).order_by(Task.id))
        tasks = result.scalars().all()

        if not tasks:
            return

        for i, task in enumerate(tasks):
            days_ago = (len(tasks) - i) * 1.5
            hours_offset = (i * 7) % 24
            task_date = now - timedelta(days=days_ago, hours=hours_offset)
            await db.execute(
                update(Task)
                .where(Task.id == task.id)
                .values(created_at=task_date)
            )

        await db.commit()
    print("Updated task dates")


async def populate() -> None:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://localhost",
    ) as client:
        await clear_existing_data()

        users: list[dict] = []

        print(f"\nCreating {len(USERS)} users...")
        for user_data in USERS:
            response = await client.post(
                "/api/users",
                json={
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "password": user_data["password"],
                },
            )
            response.raise_for_status()
            user = response.json()
            print(f"  Created: {user['username']}")

            response = await client.post(
                "/api/users/token",
                data={
                    "username": user_data["email"],
                    "password": user_data["password"],
                },
            )
            response.raise_for_status()
            token = response.json()["access_token"]

            if image_name := user_data.get("image"):
                image_path = POPULATE_IMAGES_DIR / image_name
                if image_path.exists():
                    response = await client.patch(
                        f"/api/users/{user['id']}/picture",
                        files={
                            "file": (
                                image_name,
                                image_path.read_bytes(),
                                "image/jpeg",
                            ),
                        },
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    response.raise_for_status()
                    print(f"    Uploaded: {image_name}")

            users.append({"id": user["id"], "username": user["username"], "token": token})

        print(f"\nCreating {len(TASKS)} tasks...")
        for i, task_data in enumerate(TASKS):
            user = users[i % len(users)]
            response = await client.post(
                "/api/items",
                json={
                    "title": task_data["title"],
                    "content": task_data["content"],
                    "status": task_data["status"],
                    "due_date": task_data["due_date"],
                },
                headers={"Authorization": f"Bearer {user['token']}"},
            )
            response.raise_for_status()
            title = task_data["title"]
            print(
                f"  Created: '{title[:50]}...'" if len(title) > 50 else f"  Created: '{title}'"
            )

        print("\nUpdating task dates...")
        await update_task_dates()

    await engine.dispose()

    print("\nDone!")
    print(f"  {len(USERS)} users")
    print(f"  {len(TASKS)} tasks")


if __name__ == "__main__":
    asyncio.run(populate())
