from sqlalchemy.orm import Session
from fuzzywuzzy import process, fuzz
from db.database import StandardName, AnalysisSynonym, Unit, UnitSynonym

def get_unification_name(db: Session, synonym: str, threshold: float = 80.0) -> str:
    """
    Повертає уніфіковане ім'я для заданого синоніму або найбільш схоже значення,
    якщо схожість перевищує заданий поріг.

    :param db: Сесія бази даних.
    :param synonym: Синонім або можливе уніфіковане ім'я.
    :param threshold: Поріг схожості (від 0 до 100), щоб прийняти синонім.
    :return: Уніфіковане ім'я або повідомлення про відсутність.
    """
    try:
        # Перевірка на точний збіг для синоніму
        synonym_entry = db.query(AnalysisSynonym).filter_by(synonym=synonym).first()
        if synonym_entry:
            return synonym_entry.standard_name.name  # Повертаємо уніфіковане ім'я стандартного імені

        # Перевірка на точний збіг для уніфікованого імені
        standard_entry = db.query(StandardName).filter_by(name=synonym).first()
        if standard_entry:
            return standard_entry.name  # Повертаємо уніфіковане ім'я

        # Отримуємо всі синоніми та уніфіковані імена з бази
        all_synonyms = db.query(AnalysisSynonym.synonym).all()
        all_standard_names = db.query(StandardName.name).all()

        all_synonyms_list = [item[0] for item in all_synonyms]
        all_standard_names_list = [item[0] for item in all_standard_names]

        # Об'єднуємо списки синонімів і стандартних імен для пошуку
        combined_list = all_synonyms_list + all_standard_names_list

        # Шукаємо найбільш схожий синонім або стандартне ім'я
        match, score = process.extractOne(synonym, combined_list, scorer=fuzz.ratio)

        if score >= threshold:
            # Якщо знайдено схоже значення, повертаємо тільки уніфіковане ім'я
            if match in all_synonyms_list:
                matched_entry = db.query(AnalysisSynonym).filter_by(synonym=match).first()
                return matched_entry.standard_name.name
            else:
                matched_entry = db.query(StandardName).filter_by(name=match).first()
                return matched_entry.name

        # Якщо синонім не знайдено, шукаємо найбільш схожі уніфіковані імена за частинами тексту
        partial_match, partial_score = process.extractOne(synonym, all_standard_names_list, scorer=fuzz.partial_ratio)

        if partial_score >= threshold:
            # Якщо знайдено схоже уніфіковане ім'я, повертаємо його
            partial_entry = db.query(StandardName).filter_by(name=partial_match).first()
            return partial_entry.name

        return f"Синонім '{synonym}' не знайдено в базі та немає подібних варіантів."
    except Exception as e:
        print(f"Помилка: {e}")
        return "Сталася помилка при пошуку уніфікованого імені."
