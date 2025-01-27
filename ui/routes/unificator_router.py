from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from db.get_db_session import get_db
from sqlalchemy.orm import Session
from core.unificator import get_unification_name


router = APIRouter()
templates = Jinja2Templates(directory="ui/templates")


@router.get("/unificator", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("unificator.html", {"request": request})



@router.post("/unificator", response_class=HTMLResponse)
async def process_unification_name(
        request: Request,
        db: Session = Depends(get_db),
        synonym: str = Form(...),
        threshold: float = Form(...),

):
    try:
        # Перевірка порогу схожості, якщо потрібно
        if not (0 <= threshold <= 100):
            raise HTTPException(status_code=400, detail="Поріг повинен бути між 0 і 100.")

        # Отримання результату функції уніфікації
        result = get_unification_name(db, synonym, threshold)

        # Повертаємо результат у шаблон
        return templates.TemplateResponse(
            "unificator.html",
            {"request": request, "result": result}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))