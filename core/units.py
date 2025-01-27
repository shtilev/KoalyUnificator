from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from db.database import StandardName, Unit, AnalysisSynonym
from db.database import UnitSynonym


def get_all_units(db: Session):
    all_units = db.query(Unit).all()
    return all_units


def get_units(db: Session, analysis_id: int):
    # Отримуємо всі одиниці для конкретного стандартного імені (аналізу)
    units = db.query(Unit).filter(Unit.standard_name_id == analysis_id).all()
    return [{"id": unit.id, "unit": unit.unit, "is_standard": unit.is_standard} for unit in units]


def create_unit(db: Session, analysis_id: int, unit_name: str, is_standard: bool):
    # Створення нової одиниці для стандартного імені
    unit = Unit(unit=unit_name, standard_name_id=analysis_id, is_standard=is_standard)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def update_unit(db: Session, unit_id: int, unit_name: str, is_standard: bool):
    # Оновлення одиниці
    unit = db.query(Unit).filter(Unit.id == unit_id).first()

    if not unit:
        return None

    unit.unit = unit_name
    unit.is_standard = is_standard
    db.commit()
    db.refresh(unit)
    return unit


def delete_unit(db: Session, unit_id: int):
    # Видалення одиниці
    unit = db.query(Unit).filter(Unit.id == unit_id).first()

    standard_name_id = unit.standard_name_id
    if unit:
        db.delete(unit)
        db.commit()

    return standard_name_id


def get_unit_synonyms(db: Session, unit_id: int):
    # Отримуємо всі синоніми для одиниці
    synonyms = db.query(UnitSynonym).filter(UnitSynonym.unit_id == unit_id).all()
    return [{"id": synonym.id, "synonym": synonym.synonym} for synonym in synonyms]

def add_unit_synonym(db: Session, unit_id: int, synonym: str):
    # Додаємо новий синонім для одиниці
    unit_synonym = UnitSynonym(unit_id=unit_id, synonym=synonym)
    db.add(unit_synonym)
    db.commit()
    db.refresh(unit_synonym)
    return unit_synonym

def update_unit_synonym(db: Session, synonym_id: int, new_synonym: str):
    # Пошук існуючого синоніма
    synonym = db.query(UnitSynonym).filter(UnitSynonym.id == synonym_id).first()
    if not synonym:
        return None

    # Оновлення значення синоніма
    synonym.synonym = new_synonym
    db.commit()
    db.refresh(synonym)
    return synonym

def remove_unit_synonym(db: Session, synonym_id: int):
    # Видаляємо синонім одиниці
    synonym = db.query(UnitSynonym).filter(UnitSynonym.id == synonym_id).first()

    if synonym:
        db.delete(synonym)
        db.commit()
        return True

    return False



def remove_standard_units(db: Session, unit_id: int):
    # Обновляем все юниты, снимая отметку стандарту для тех юнитов, которые не равны unit_id
    units = db.query(Unit).filter(Unit.standard_name_id == db.query(Unit.standard_name_id).filter(Unit.id == unit_id).first().standard_name_id).all()
    for unit in units:
        if unit.id != unit_id:
            unit.is_standard = False
    db.commit()
