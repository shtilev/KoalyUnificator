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
from core.units import delete_unit, update_unit, create_unit, remove_standard_units
from core.generator import create_synonyms_for_standard_name
from db.get_db_session import get_db
from sqlalchemy.orm import Session
import os
import logging

logger = logging.getLogger("__name__")


router = APIRouter()

templates = Jinja2Templates(directory="ui/templates")


@router.get("/analysis", response_class=HTMLResponse)
async def get_all_analysis(request: Request, filter_letter: str = None, db: Session = Depends(get_db)):
    analyses = get_analysis(db)
    if filter_letter:
        analyses = [analysis for analysis in analyses if analysis['name'].startswith(filter_letter)]

    return templates.TemplateResponse("analysis.html", {
        "request": request,
        "analyses": analyses,
        "filter_letter": filter_letter,
    })


@router.post("/add_analyse")
async def add_analysis(
    standard_name: str = Form(...),
    synonym: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        create_analysis(db, analysis_name=standard_name, synonym=synonym)
    except ValueError as e:
        return {"error": str(e)}

    return RedirectResponse(url="/analysis", status_code=303)



@router.post("/delete_analyse")
async def remove_analyse(analysis_id: int = Form(...),
                         db: Session = Depends(get_db)):
    delete_analysis(db, analysis_id)
    return RedirectResponse(url="/analysis", status_code=303)


@router.get("/analysis/{analysis_id}", response_class=HTMLResponse)
def read_analysis_detail(analysis_id: int, request: Request, db: Session = Depends(get_db)):
    analysis_detail = get_analysis_detail(db, analysis_id)
    if not analysis_detail:
        raise HTTPException(status_code=404, detail="Analysis not found")

    synonyms_count = len(analysis_detail["synonyms"])

    return templates.TemplateResponse(
        "analysis_detail.html",
        {
            "request": request,
            "analysis": {
                "id": analysis_detail["id"],
                "name": analysis_detail["name"],
                "standard_unit": analysis_detail["standard_unit"],
                "units": analysis_detail["units"],
            },
            "synonyms": analysis_detail["synonyms"],
            "synonyms_count": synonyms_count
        }
    )


@router.post("/add_analysis_synonym")
async def add_synonym(analysis_id: int = Form(...), synonym: str = Form(...), db: Session = Depends(get_db)):
    # Добавление нового синонима
    add_analysis_synonym(db, analysis_id, synonym)
    return RedirectResponse(url=f"/analysis/{analysis_id}", status_code=303)


@router.post("/remove_analysis_synonym")
async def remove_synonym(synonym_id: int = Form(...), db: Session = Depends(get_db)):
    # Удаление синонима
    remove_analysis_synonym(db, synonym_id)
    return RedirectResponse(url=f"/analysis", status_code=303)
    raise HTTPException(status_code=404, detail="Synonym not found")


@router.post("/update_analysis_synonym")
async def update_synonym(synonym_id: int = Form(...),
                         new_synonym: str = Form(...),
                         db: Session = Depends(get_db)):
    # Оновлення синоніма
    updated_synonym = update_analysis_synonym(db, synonym_id, new_synonym)
    if updated_synonym:
        return RedirectResponse(url=f"/analysis/{updated_synonym.standard_name_id}", status_code=303)
    raise HTTPException(status_code=404, detail="Synonym not found")


@router.post("/generate_analyse_synonym", response_class=HTMLResponse)
async def generate_analyse_synonym(request: Request,
                                   db: Session = Depends(get_db),
                                   analysis_id: int = Form(...),
                                   count: int = Form(...)):
    for _ in range(count):
        create_synonyms_for_standard_name(db, analysis_id)

    return RedirectResponse(url=f"/analysis/{analysis_id}", status_code=303)


@router.post("/add_unit")
async def add_unit(
        analysis_id: int = Form(...),
        unit_name: str = Form(...),
        is_standard: bool = Form(default=False),
        db: Session = Depends(get_db)
):
    try:

        create_unit(db, analysis_id=analysis_id, unit_name=unit_name, is_standard=is_standard)
    except ValueError as e:
        return {"error": str(e)}

    return RedirectResponse(url=f"/analysis/{analysis_id}", status_code=303)


@router.post("/delete_unit")
async def remove_unit(unit_id: int = Form(...), db: Session = Depends(get_db)):
    # Видалення одиниці
    unit = delete_unit(db, unit_id)

    return RedirectResponse(url=f"/analysis/{unit}", status_code=303)


@router.post("/update_unit")
async def update_unit_route(
        unit_id: int = Form(...),
        unit_name: str = Form(...),
        is_standard: bool = Form(False),
        db: Session = Depends(get_db)
):
    logger.error(f"Received unit_id: {unit_id}, unit_name: {unit_name}, is_standard: {is_standard}")

    # Оновлення одиниці
    updated_unit = update_unit(db, unit_id=unit_id, unit_name=unit_name, is_standard=is_standard)

    # Якщо юніт оновлений
    if updated_unit:
        # Якщо встановлений новий стандартний юніт, зняти стандарт з попереднього
        if is_standard:
            # Знімаємо стандарт з усіх інших юнітів
            remove_standard_units(db, unit_id)
        return RedirectResponse(url=f"/analysis/{updated_unit.standard_name_id}", status_code=303)

    raise HTTPException(status_code=404, detail="Unit not found")


@router.post("/remove_selected_synonyms")
async def remove_selected_synonyms(selected_synonyms: list[int] = Form(...), db: Session = Depends(get_db)):
    if not selected_synonyms:
        raise HTTPException(status_code=400, detail="No synonyms selected for deletion")

    # Видалення вибраних синонімів
    for synonym_id in selected_synonyms:
        remove_analysis_synonym(db, synonym_id)

    return RedirectResponse(url="/analysis", status_code=303)

