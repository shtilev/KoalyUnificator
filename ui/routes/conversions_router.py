from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from core.conversions import (get_all_conversions,
                              create_conversion,
                              delete_conversion,
                              get_conversions_by_standard_name,
                              update_conversion)
from core.analysis import get_analysis, get_analysis_detail
from core.generator import generate_unit_conversions_for_standard_name
from core.units import get_units
from db.get_db_session import get_db
from sqlalchemy.orm import Session
import os
import logging

logger = logging.getLogger("__name__")


router = APIRouter()

templates = Jinja2Templates(directory="ui/templates")


@router.get("/conversions", response_class=HTMLResponse)
async def get_all_conversions(request: Request, filter_letter: str = None, db: Session = Depends(get_db)):
    analyses = get_analysis(db)
    if filter_letter:
        analyses = [analysis for analysis in analyses if analysis['name'].startswith(filter_letter)]

    return templates.TemplateResponse("conversions.html", {
        "request": request,
        "analyses": analyses,
        "filter_letter": filter_letter,
    })


@router.get("/conversions/{analysis_id}", response_class=HTMLResponse)
def read_conversions_for_analyse(analysis_id: int, request: Request, db: Session = Depends(get_db)):
    conversions = get_conversions_by_standard_name(db, analysis_id)
    analysis_name = get_analysis_detail(db, analysis_id).get('name')
    units = get_units(db, analysis_id)

    return templates.TemplateResponse(
        "conversion_detail.html",
        {
            "request": request,
            "analysis_name": analysis_name,
            "analysis_id": analysis_id,
            "conversions": conversions,
            "units": units,
        }
    )


@router.post("/create_conversion")
def add_conversion(
    standard_name_id: int = Form(...),
    from_unit_id: int = Form(...),
    to_unit_id: int = Form(...),
    formula: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Додати нову конверсію.
    """
    conversion = create_conversion(db, standard_name_id, from_unit_id, to_unit_id, formula)
    if not conversion:
        raise HTTPException(status_code=400, detail="Не вдалося створити конверсію.")
    return RedirectResponse(f"/conversions/{standard_name_id}", status_code=303)


@router.post("/update_conversion")
def update_conversion_router(
        conversion_id: int = Form(...),
        formula: str = Form(...),
        db: Session = Depends(get_db)
):
    """
    Оновити конверсію (тільки формулу).
    """
    conversion = update_conversion(db, conversion_id, formula=formula)
    if not conversion:
        raise HTTPException(status_code=404, detail="Конверсію не знайдено.")

    # Перенаправляем на страницу с подробностями конверсии
    return RedirectResponse(f"/conversions/{conversion['standard_name_id']}", status_code=303)


@router.post("/delete_conversion")
def delete_conversion_router(
    conversion_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Видалити конверсію.
    """
    deleted_conversion = delete_conversion(db, conversion_id)
    if not deleted_conversion:
        raise HTTPException(status_code=404, detail="Конверсію не знайдено.")
    return RedirectResponse(f"/conversions/{deleted_conversion['standard_name_id']}", status_code=303)


@router.post("/generate_conversion")
def gen_conversion(standard_name_id: int = Form(...),
    db: Session = Depends(get_db)):
    generate_unit_conversions_for_standard_name(db, standard_name_id)
    return RedirectResponse(f"/conversions/{standard_name_id}", status_code=303)

