from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.database import UnitConversion, Unit, StandardName
from typing import Dict



def convert_units_logic(value: float, from_unit_id: int, standard_name_id: int, db: Session) -> Dict:
    # Перевірка наявності одиниці
    from_unit = db.query(Unit).filter(Unit.id == from_unit_id).first()
    if not from_unit:
        raise HTTPException(status_code=404, detail="Unit not found.")

    # Перевірка наявності стандартного імені
    standard_name = db.query(StandardName).filter(StandardName.id == standard_name_id).first()
    if not standard_name:
        raise HTTPException(status_code=404, detail="Standard name not found.")

    # Отримуємо список конверсій для стандартного імені
    conversions = db.query(UnitConversion).filter(UnitConversion.standard_name_id == standard_name_id).all()

    results = {}
    for conversion in conversions:
        if conversion.from_unit_id == from_unit.id:
            # Використовуємо формулу для обчислення
            formula = conversion.formula.replace("x", str(value))
            try:
                converted_value = eval(formula)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Formula error: {str(e)}")

            # Зберігаємо результат конверсії
            results[conversion.to_unit_id] = converted_value

    return results
