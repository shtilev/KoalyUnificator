from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from core.dynamic import add_to_dynamic, get_all_dynamic_entries, remove_from_dynamic
from core.analysis import get_analysis
from db.get_db_session import get_db
from sqlalchemy.orm import Session
import os
import logging


logger = logging.getLogger("__name__")


router = APIRouter()

templates = Jinja2Templates(directory="ui/templates")


@router.get("/dynamic", response_class=HTMLResponse)
async def get_all_dynamics(request: Request, db: Session = Depends(get_db)):
    dynamics = get_all_dynamic_entries(db)
    analysis = get_analysis(db)
    return templates.TemplateResponse("dynamic.html", {
        "request": request,
        "dynamic": dynamics,
        "analysis_list": analysis
    })


@router.post("/add_dynamic")
async def add_d(
    analysis_id: int = Form(...),
    db: Session = Depends(get_db)
):
    try:
        x = add_to_dynamic(db, analysis_id=analysis_id)
        logger.info(f'Add: {x}')
    except ValueError as e:
        return {"error": str(e)}

    return RedirectResponse(url="/dynamic", status_code=303)



@router.post("/delete_dynamic")
async def remove_analyse(analysis_id: int = Form(...),
                         db: Session = Depends(get_db)):
    remove_from_dynamic(db, analysis_id)
    return RedirectResponse(url="/dynamic", status_code=303)



