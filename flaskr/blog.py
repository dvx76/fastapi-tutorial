from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(include_in_schema=False)

fake_posts_db = [
    {
        "id": 1,
        "username": "Bob",
        "title": "Bob is awesome",
        "body": "Everybody loves Bob!",
        "created": "2026-01-03",
    },
    {
        "id": 2,
        "username": "Bob",
        "title": "Easy title",
        "body": "Easy post",
        "created": "2026-01-02",
    },
    {
        "id": 3,
        "username": "Alice",
        "title": "Alice is awesome too",
        "body": "<3",
        "created": "2026-01-01",
    },
]


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request, name="blog/index.html.j2", context={"posts": fake_posts_db}
    )


@router.get("/create", response_class=HTMLResponse)
@router.post("/create", response_class=HTMLResponse)
def create():
    return "Dummy"


# @router.post("/update", response_class=HTMLResponse)
@router.get("/update/{id}", response_class=HTMLResponse)
def update(id: str):
    return "Dummy"
