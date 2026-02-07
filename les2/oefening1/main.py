from datetime import datetime, timezone

from fastapi import Cookie, FastAPI, HTTPException, Path, Query, Response, status
from pydantic import BaseModel, Field
from typing_extensions import Annotated

app = FastAPI(title="Task Management API", version="1.0.0")

TASKS_DB: dict[int, "TaskInternal"] = {}


class TaskCreate(BaseModel):
    title: Annotated[str, Field(min_length=3, examples=["Learn FastAPI"])]
    description: Annotated[str | None, Field(examples=["Use the FastAPI tutorial"])] = (
        None
    )
    priority: Annotated[int, Field(ge=1, le=5, examples=[4])]


class TaskExternal(TaskCreate):
    task_id: Annotated[int, Field(serialization_alias="id", examples=[1])]


class TaskInternal(TaskExternal):
    created_at: Annotated[
        datetime, Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    ]


class TaskUpdate(TaskCreate):
    title: Annotated[str | None, Field(min_length=3)] = None
    priority: Annotated[int | None, Field(ge=1, le=5)] = None


class Preference(BaseModel):
    min_priority: Annotated[int, Field(ge=1, le=5)]


TaskId = Annotated[int, Path(ge=1)]


@app.post(
    "/tasks",
    response_model=TaskExternal,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
    summary="Create a new task",
)
def create_task(task: TaskCreate):
    next_task_id = max(TASKS_DB.keys(), default=0) + 1
    new_task = TaskInternal(task_id=next_task_id, **task.model_dump())

    TASKS_DB[next_task_id] = new_task

    return new_task


@app.get(
    "/tasks/{task_id}",
    response_model=TaskExternal,
    tags=["Tasks"],
    summary="Get a single task",
)
def get_task(task_id: TaskId):
    try:
        return TASKS_DB[task_id]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )


@app.get(
    "/tasks", response_model=list[TaskExternal], tags=["Tasks"], summary="List tasks"
)
def list_tasks(
    min_priority: Annotated[int | None, Query(ge=1)] = None,
    query: Annotated[str | None, Query(alias="q", min_length=3)] = None,
    cookie_min_priority: Annotated[
        int | None, Cookie(alias="min_priority", include_in_schema=False)
    ] = None,
):
    results = TASKS_DB.values()

    if min_priority is None and cookie_min_priority is not None:
        min_priority = cookie_min_priority

    if min_priority is not None:
        results = [t for t in results if t.priority >= min_priority]

    if query:
        results = [t for t in results if query.lower() in t.title.lower()]

    return results


@app.patch(
    "/tasks/{task_id}",
    response_model=TaskExternal,
    tags=["Tasks"],
    summary="Update a task",
)
def update_task(task_id: TaskId, task_data: TaskUpdate):
    stored_task = TASKS_DB.get(task_id)
    if not stored_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    update_data = task_data.model_dump(exclude_unset=True)
    updated_task = stored_task.model_copy(update=update_data)

    TASKS_DB[task_id] = updated_task
    return updated_task


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
