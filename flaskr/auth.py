from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/auth", include_in_schema=False)


@router.get("/create", response_class=HTMLResponse)
@router.post("/create", response_class=HTMLResponse)
def register(request: Request):
    return "Dummy"


@router.get("/login", response_class=HTMLResponse)
@router.post("/login", response_class=HTMLResponse)
def login(request: Request):
    return "Dummy"


@router.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    return "Dummy"
