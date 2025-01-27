import json

from fastapi.params import Depends

from core.units import create_unit
from core.analysis import create_analysis
from core.conversions import create_conversion
from db.get_db_session import get_db
from db.database import SessionLocal
from tqdm import tqdm
from sqlalchemy.orm import Session



def save_data_to_db(json_path):
    """
    Зберігає дані з JSON у базу даних.

    :param json_path: Шлях до файлу JSON
    """
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)


    db = SessionLocal()
    for analysis in tqdm(data, desc="Збереження записів", unit="записів"):
        # Отримуємо назву аналізу
        analysis_name = analysis.get('analysis-name')

        # Створюємо запис для аналізу
        try:
            analysis_entry = create_analysis(db, analysis_name, analysis_name)
        except ValueError as e:
            print(f"Аналіз '{analysis_name}' вже існує: {e}")
            continue

        analysis_id = analysis_entry.id

        # Обробка одиниць вимірювання
        units = set()
        for calc in analysis.get('calculator', []):
            units.add(calc['from'])
            units.add(calc['to'])

        unit_ids = {}
        for unit_name in units:
            is_standard = unit_name == list(units)[0]  # Вважаємо перший елемент стандартним
            unit_entry = create_unit(db, analysis_id, unit_name, is_standard)
            unit_ids[unit_name] = unit_entry.id

        # Обробка конверсій
        for calc in analysis.get('calculator', []):
            from_unit_id = unit_ids.get(calc['from'])
            to_unit_id = unit_ids.get(calc['to'])
            formula = calc['formula']

            create_conversion(db, analysis_id, from_unit_id, to_unit_id, formula)

    print("Дані успішно збережено до бази даних.")

# Виклик функції
save_data_to_db('results.json')
