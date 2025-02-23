import json
from datetime import datetime
from db.database import SessionLocal, AnalysisSynonym, StandardName


def export_dataset():
    session = SessionLocal()
    dataset = []

    synonyms = session.query(AnalysisSynonym).join(StandardName).all()

    for synonym in synonyms:
        dataset.append({
            "text": synonym.synonym,
            "label": synonym.standard_name.id
        })

    session.close()

    # Получаем текущую дату в формате YYYY-MM-DD
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Формируем имя файла с датой
    filename = f"dataset/dataset_{current_date}.json"

    # Сохраняем файл
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"Success saved to {filename}")


export_dataset()
