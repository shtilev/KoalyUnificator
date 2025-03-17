import json
from datetime import datetime
from db.database import SessionLocal, AnalysisSynonym, StandardName, Dynamic


def export_dataset():
    session = SessionLocal()
    dataset = []

    synonyms = session.query(AnalysisSynonym).join(StandardName).all()

    for synonym in synonyms:
        dataset.append({
            "text": synonym.synonym,
            "label": synonym.standard_name.name
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


def export_dynamic_dataset():
    session = SessionLocal()
    dataset = []

    # Витягуємо тільки ті аналізи, які є в таблиці dynamic
    dynamic_synonyms = (
        session.query(AnalysisSynonym)
        .join(StandardName)
        .join(Dynamic, Dynamic.analysis_id == StandardName.id)
        .all()
    )

    for synonym in dynamic_synonyms:
        # В label добавляем только унифицированное название из StandardName
        dataset.append({
            "text": synonym.synonym.strip(),  # Синоним
            "label": synonym.standard_name.name.strip()  # Унифицированное название анализа
        })

    session.close()

    # Удаляем дубликаты по text и label
    dataset = [dict(t) for t in {tuple(d.items()) for d in dataset}]

    # Формируем имя файла с датой
    current_date = datetime.now().strftime("%Y-%m-%d")
    filename = f"dataset/dynamic_dataset_{current_date}.json"

    # Сохраняем JSON-файл
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"✅ Success saved to {filename}")

# export_dynamic_dataset()
export_dataset()