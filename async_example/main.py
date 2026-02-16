from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql.functions import current_timestamp
from typing_extensions import Annotated


# FastAPI Pydantic Models
class TaskCreate(BaseModel):
    title: Annotated[str, Field(min_length=3, examples=["Learn FastAPI"])]
    description: Annotated[str | None, Field(examples=["Use the FastAPI tutorial"])] = (
        None
    )
    priority: Annotated[int, Field(ge=1, le=5, examples=[4])]


class TaskExternal(TaskCreate):
    task_id: Annotated[int, Field(serialization_alias="id", examples=[1])]


class TaskUpdate(TaskCreate):
    title: Annotated[str | None, Field(min_length=3)] = None
    priority: Annotated[int | None, Field(ge=1, le=5)] = None


class Preference(BaseModel):
    min_priority: Annotated[int, Field(ge=1, le=5)]


TaskId = Annotated[int, Path(ge=1)]


# SQLAlchemy Models
class Base(DeclarativeBase):
    pass


class StoredTask(Base):
    __tablename__ = "todos"

    task_id: Mapped[int] = mapped_column(
        name="id", primary_key=True, autoincrement=True
    )
    title: Mapped[str]
    description: Mapped[str]
    priority: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(server_default=current_timestamp())


DATABASE_URL = "sqlite+aiosqlite:///./tasks.db"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created")
    yield


app = FastAPI(title="Task Management API", version="1.0.0", lifespan=lifespan)


async def get_db():
    """Provides a database session for each request"""
    async with AsyncSessionLocal() as session:
        yield session


@app.post(
    "/tasks",
    response_model=TaskExternal,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
    summary="Create a new task",
)
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
    new_task = StoredTask(**task.model_dump())
    db.add(new_task)
    await db.commit()

    return new_task


@app.get(
    "/tasks/{task_id}",
    response_model=TaskExternal,
    tags=["Tasks"],
    summary="Get a single task",
)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(StoredTask, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@app.get(
    "/tasks",
    response_model=list[TaskExternal],
    tags=["Tasks"],
    summary="List tasks",
)
async def list_tasks(
    min_priority: Annotated[int | None, Query(ge=1)] = None,
    query: Annotated[str | None, Query(alias="q", min_length=3)] = None,
    cookie_min_priority: Annotated[
        int | None, Cookie(alias="min_priority", include_in_schema=False)
    ] = None,
    db: AsyncSession = Depends(get_db),
):
    db_query = select(StoredTask)

    if min_priority is None and cookie_min_priority is not None:
        min_priority = cookie_min_priority

    if min_priority is not None:
        db_query = db_query.where(StoredTask.priority >= min_priority)

    if query:
        db_query = db_query.where(func.lower(StoredTask.title.contains(query.lower())))

    print(f"Using query: {db_query}")

    result = await db.scalars(db_query)
    return result.all()


@app.patch(
    "/tasks/{task_id}",
    response_model=TaskExternal,
    tags=["Tasks"],
    summary="Update a task",
)
async def update_task(
    task_id: int, task_data: TaskUpdate, db: AsyncSession = Depends(get_db)
):
    stored_task = await db.get(StoredTask, task_id)
    if stored_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stored_task, field, value)

    await db.commit()
    return stored_task


@app.post(
    "/preferences",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Preferences"],
    summary="Set user preferences",
)
def set_preferences(pref: Preference, response: Response):
    response.set_cookie(
        key="min_priority",
        value=str(pref.min_priority),
    )
