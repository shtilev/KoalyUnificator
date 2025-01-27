from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from core.analysis import (get_analysis,
                           create_analysis,
                           get_analysis_synonyms,
                           get_analysis_detail,
                           add_analysis_synonym,
                           remove_analysis_synonym,
                           update_analysis_synonym,
                           delete_analysis)
from core.units import delete_unit, update_unit, create_unit, remove_standard_units, get_units
from core.generator import create_synonyms_for_standard_name
from core.calclulator import convert_units_logic
from db.get_db_session import get_db
from sqlalchemy.orm import Session
import os
import logging
from typing import Dict




router = APIRouter()

templates = Jinja2Templates(directory="ui/templates")


@router.get("/calculator", response_class=HTMLResponse)
async def calculator_route(request: Request, filter_letter: str = None, db: Session = Depends(get_db)):
    analyses = get_analysis(db)
    if filter_letter:
        analyses = [analysis for analysis in analyses if analysis['name'].startswith(filter_letter)]

    return templates.TemplateResponse("calculator.html", {
        "request": request,
        "analyses": analyses,
        "filter_letter": filter_letter,
    })




# Роут для відображення результатів конверсії
@router.get("/calculator_result/{standard_name_id}", response_class=HTMLResponse)
async def show_conversion_form(request: Request, standard_name_id: int, db: Session = Depends(get_db)):
    # Отримуємо стандартне ім'я за id
    standard_name = get_analysis_detail(db, standard_name_id).get('name')
    if not standard_name:
        raise HTTPException(status_code=404, detail="Standard name not found.")
    # Отримуємо одиниці вимірювання для цього стандартного імені
    units = get_units(db, standard_name_id)

    # Відправляємо шаблон для конкретного аналізу
    return templates.TemplateResponse("calculator_result.html", {
        "request": request,
        "standard_name": standard_name,
        "standard_name_id": standard_name_id,
        "units": units
    })

# Роут для конверсії одиниць
@router.post("/convert_units")
async def convert_units_api(request: Dict, db: Session = Depends(get_db)):
    value = request.get("value")
    from_unit_id = request.get("from_unit_id")
    standard_name_id = request.get("standard_name_id")

    # Перевіряємо, чи всі необхідні параметри надано
    if not value or not from_unit_id or not standard_name_id:
        raise HTTPException(status_code=400, detail="Missing parameters")

    # Викликаємо конверсію одиниць
    results = convert_units_logic(value, from_unit_id, standard_name_id, db)

    return {"results": results}