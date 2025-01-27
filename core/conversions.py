from sqlalchemy.orm import Session
from db.database import UnitConversion, StandardName, Unit


def get_all_conversions(db: Session):
    """
    Отримати всі конверсії одиниць.
    """
    conversions = db.query(UnitConversion).all()
    return [
        {
            "id": conv.id,
            "from_unit_id": conv.from_unit_id,
            "to_unit_id": conv.to_unit_id,
            "formula": conv.formula,
            "standard_name_id": conv.standard_name_id,
        }
        for conv in conversions
    ]

def get_conversions_by_standard_name(db: Session, standard_name_id: int):
    """
    Отримати всі конверсії для конкретного стандартного імені з назвами одиниць.
    """
    conversions = db.query(UnitConversion).filter(UnitConversion.standard_name_id == standard_name_id).all()
    return [
        {
            "id": conv.id,
            "from_unit_id": conv.from_unit_id,
            "from_unit_name": conv.from_unit.unit,
            "to_unit_id": conv.to_unit_id,
            "to_unit_name": conv.to_unit.unit,
            "formula": conv.formula,
        }
        for conv in conversions
    ]


def create_conversion(db: Session, standard_name_id: int, from_unit_id: int, to_unit_id: int, formula: str):
    """
    Створити нову конверсію одиниць.
    """
    conversion = UnitConversion(
        standard_name_id=standard_name_id,
        from_unit_id=from_unit_id,
        to_unit_id=to_unit_id,
        formula=formula,
    )
    db.add(conversion)
    db.commit()
    db.refresh(conversion)
    return {
        "id": conversion.id,
        "from_unit_id": conversion.from_unit_id,
        "to_unit_id": conversion.to_unit_id,
        "formula": conversion.formula,
        "standard_name_id": conversion.standard_name_id,
    }


def update_conversion(db: Session, conversion_id: int, formula: str):
    """
    Оновити існуючу конверсію одиниць (тільки формулу).
    """
    conversion = db.query(UnitConversion).filter(UnitConversion.id == conversion_id).first()

    if not conversion:
        return None

    # Обновляем только формулу
    conversion.formula = formula
    db.commit()
    db.refresh(conversion)

    return {
        "id": conversion.id,
        "from_unit_id": conversion.from_unit_id,
        "to_unit_id": conversion.to_unit_id,
        "formula": conversion.formula,
        "standard_name_id": conversion.standard_name_id,
    }


def delete_conversion(db: Session, conversion_id: int):
    """
    Видалити конверсію одиниць за її ID та повернути ID стандартного імені (аналізу).
    """
    conversion = db.query(UnitConversion).filter(UnitConversion.id == conversion_id).first()

    if not conversion:
        return None

    # Получаем standard_name_id через связь с таблицей Unit
    standard_name_id = db.query(Unit.standard_name_id).filter(Unit.id == conversion.from_unit_id).first()

    if not standard_name_id:
        return None

    # Удаляем запись
    db.delete(conversion)
    db.commit()

    # Возвращаем id конверсии и стандартное имя
    return {"id": conversion_id,
            "standard_name_id": standard_name_id[0]}
