from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from db.database import StandardName, Unit, AnalysisSynonym

def get_analysis(db: Session):
    # Отримуємо всі стандартні імена разом із стандартними одиницями та синонімами
    analyses = db.query(StandardName).options(
        joinedload(StandardName.units),
        joinedload(StandardName.synonyms)
    ).all()
    result = []

    for analysis in analyses:
        # Витягуємо стандартну одиницю, якщо вона є
        standard_unit = next((unit.unit for unit in analysis.units if unit.is_standard), None)

        # Отримуємо список усіх одиниць
        units = [unit.unit for unit in analysis.units]

        # Отримуємо список синонімів
        synonyms = [synonym.synonym for synonym in analysis.synonyms]

        analysis_data = {
            "id": analysis.id,
            "name": analysis.name,
            "standard_unit": standard_unit,
            "units": units,
            "synonyms": synonyms
        }

        result.append(analysis_data)

    return result

def get_analysis_detail(db: Session, analysis_id: int):
    # Отримуємо аналіз за ID з усіма пов'язаними одиницями та синонімами
    analysis = db.query(StandardName).options(
        joinedload(StandardName.units),
        joinedload(StandardName.synonyms)
    ).filter(StandardName.id == analysis_id).first()

    if not analysis:
        return None

    standard_unit = next(({"id": unit.id, "unit": unit.unit} for unit in analysis.units if unit.is_standard), None)
    units = [{"id": unit.id, "unit": unit.unit} for unit in analysis.units]
    synonyms = [{"id": synonym.id, "synonym": synonym.synonym} for synonym in analysis.synonyms]

    analysis_detail = {
        "id": analysis.id,
        "name": analysis.name,
        "standard_unit": standard_unit,
        "units": units,
        "synonyms": synonyms
    }

    return analysis_detail

def create_analysis(db: Session, analysis_name: str, synonym: str):
    # Перевірка, чи існує стандартне ім'я
    existing_analysis = db.query(StandardName).filter(StandardName.name == analysis_name).first()
    if existing_analysis:
        raise ValueError(f"Standard name '{analysis_name}' already exists.")

    # Створення нового стандартного імені
    analysis = StandardName(name=analysis_name)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Додавання синоніма
    synonym_entry = AnalysisSynonym(standard_name_id=analysis.id, synonym=synonym)
    db.add(synonym_entry)
    db.commit()
    db.refresh(synonym_entry)

    return analysis


def update_analysis(db: Session, analysis_id: int, analysis_name: str, standard_unit: str, units: list):
    # Оновлення існуючого стандартного імені
    analysis = db.query(StandardName).filter(StandardName.id == analysis_id).first()

    if not analysis:
        return None

    analysis.name = analysis_name

    # Видаляємо старі одиниці
    db.query(Unit).filter(Unit.standard_name_id == analysis.id).delete()

    # Додаємо нові одиниці
    for unit_name in units:
        unit = Unit(unit=unit_name, standard_name_id=analysis.id, is_standard=(unit_name == standard_unit))
        db.add(unit)

    db.commit()
    return analysis

def delete_analysis(db: Session, analysis_id: int):
    # Видаляємо стандартне ім'я та всі пов'язані записи
    analysis = db.query(StandardName).filter(StandardName.id == analysis_id).first()

    if analysis:
        db.query(Unit).filter(Unit.standard_name_id == analysis.id).delete()
        db.query(AnalysisSynonym).filter(AnalysisSynonym.standard_name_id == analysis.id).delete()
        db.delete(analysis)
        db.commit()
        return analysis

    return None

def get_analysis_synonyms(db: Session, analysis_id: int):
    # Отримуємо всі синоніми для стандартного імені
    synonyms = db.query(AnalysisSynonym).filter(AnalysisSynonym.standard_name_id == analysis_id).all()
    return [{"id": synonym.id, "synonym": synonym.synonym} for synonym in synonyms]

def add_analysis_synonym(db: Session, analysis_id: int, synonym: str):
    # Додаємо новий синонім
    analysis_synonym = AnalysisSynonym(standard_name_id=analysis_id, synonym=synonym)
    db.add(analysis_synonym)
    db.commit()
    db.refresh(analysis_synonym)
    return analysis_synonym

def update_analysis_synonym(db: Session, synonym_id: int, new_synonym: str):
    # Пошук існуючого синоніма
    synonym = db.query(AnalysisSynonym).filter(AnalysisSynonym.id == synonym_id).first()
    if not synonym:
        return None

    # Оновлення значення синоніма
    synonym.synonym = new_synonym
    db.commit()
    db.refresh(synonym)
    return synonym


def remove_analysis_synonym(db: Session, synonym_id: int):
    # Видаляємо синонім
    synonym = db.query(AnalysisSynonym).filter(AnalysisSynonym.id == synonym_id).first()

    if synonym:
        db.delete(synonym)
        db.commit()
        return True

    return False
