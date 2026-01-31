from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from . import auth, blog

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

app.include_router(blog.router)
app.include_router(auth.router)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.middleware("http")
async def get_user(request: Request, call_next):
    request.state.user = "Fabrice"
    return await call_next(request)
