import openai
from db.database import SessionLocal
from pydantic import BaseModel
from typing import List
from core.analysis import add_analysis_synonym, get_analysis_detail
from db.database import AnalysisSynonym, StandardName, Unit, UnitConversion
from tqdm import tqdm
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()
API_KEY_MLAI = os.getenv("API_KEY_MLAI")

client = openai.OpenAI(
    base_url="https://api.aimlapi.com/v1",
    api_key=API_KEY_MLAI
)




class SynonymsList(BaseModel):
    list_of_synonyms: List[str]


class Conversions(BaseModel):
    unit_from_id: int
    unit_to_id: int
    formula: str
    reverse_formula: str



def get_llm_response(prompt: str, response_model, model="gpt-4o-mini"):
    """
    Отримуємо відповідь від LLM (OpenAI) для синонімів до заданого уніфікованого імені.
    :param text: Вхідний текст (стандартне ім'я для якого шукаються синоніми).
    :param prompt: Повідомлення, яке передається в систему як частина запиту.
    :param response_model: Pydantic модель відповіді від ЛЛМ
    :param model: Модель, яку використовуємо для запиту.
    :return: Список синонімів у вигляді словників.
    """
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
        ],
        response_format=response_model,
        max_tokens=16384
    )
    # Парсимо відповідь у вигляді List of dicts [{standard_name: synonym}]
    reasoning_dict = completion.choices[0].message.parsed.model_dump()
    return reasoning_dict


def create_synonyms_for_standard_name(db: Session, standard_name_id: int):

    added_synonyms = []

    analyse_info = get_analysis_detail(db, standard_name_id)
    standard_name = analyse_info.get('name')
    synonyms = analyse_info.get('synonyms')
    try:
        # Формулюємо запит до OpenAI
        prompt = f"""
        Перелічіть усі можливі варіанти написання для медичного терміну: {standard_name}. Усі варіанти мають стосуватися виключно цього показника ({standard_name}) і враховувати можливі написання, які можуть зустрічатися в різних медичних документах, лабораторних результатах, аналізах тощо. 
        Включіть варіанти з такими особливостями: 
        - Різні абревіатури або скорочення (наприклад, 'Гемоглобін' > 'HGB', 'Hb').
        - Варіанти з уточненнями (наприклад, '{standard_name} у крові', ' Тест на {standard_name}' - додавай реальні приклади з медичних аналізів і інших документів).
        - Переклади та альтернативні назви (наприклад, 'Гемоглобін', 'Hemoglobin', 'Hgb'). Орієнтуйся на назви для україньского сегменту.
        - Можливі помилки або варіації у написанні, якщо вони поширені у реальних документах.

        Не включайте значення, що належать іншим показникам навіть із подібними назвами (наприклад, 'Гемоглобін А' або 'Глікогемоглобін' не слід включати).
        
        В базе вже є (їх не потрібно додавати):{str(synonyms)}
        """
        print(prompt)
        response_dict = get_llm_response(prompt, SynonymsList)

        # Перевірка наявності синонімів у відповіді
        if "list_of_synonyms" in response_dict:
            list_of_synonyms = response_dict["list_of_synonyms"]
            for synonym_data in list_of_synonyms:
                # Перевіряємо, чи вже існує синонім для цього стандартного імені
                existing_synonym = db.query(AnalysisSynonym).join(StandardName).filter(
                    StandardName.id == standard_name_id,
                    AnalysisSynonym.synonym == synonym_data
                ).first()

                if not existing_synonym:
                    # Якщо синоніма немає, додаємо його
                    add_analysis_synonym(db, standard_name_id, synonym_data)
                    added_synonyms.append(synonym_data)  # Додаємо до списку доданих синонімів
                    print(f'Синонім {synonym_data} для {standard_name} успішно додано')
                else:
                    print(f"Синонім '{synonym_data}' для '{standard_name}' вже існує.")

        return added_synonyms
    finally:
        db.close()

#TODO
def generate_unit_conversions_for_standard_name(db: Session, standard_name_id: int):
    """
    Генерує список унікальних пар одиниць вимірювання для заданого standard_name_id
    і зберігає їх у базі даних.

    :param standard_name_id: ID стандартного імені для генерації та збереження пар.
    :return: Статус операції.
    """
    unit_pairs = []

    try:
        # Отримуємо standard_name за ID
        standard_name = db.query(StandardName).filter(StandardName.id == standard_name_id).first()

        if not standard_name:
            print(f"StandardName з ID {standard_name_id} не знайдено.")
            return []

        units = standard_name.units

        for from_unit in units:
            for to_unit in units:
                if from_unit.id != to_unit.id:
                    # Додаємо пару одиниць у список як кортеж (ID, назва)
                    unit_pairs.append(
                        f'Пара із "{from_unit.unit}" (ID: {from_unit.id}) в "{to_unit.unit}" (ID: {to_unit.id}) для показника {standard_name.name}'
                    )

        for pair in unit_pairs:

            prompt = f"""
            Ми робимо розмітку конверсій для медичних показників, враховуючи специфіку аналізу. Зараз потрібно зробити конверсію між **{str(pair)}**.

            Зауваження:
            1. Поля unit_from_id/unit_to_id повинні містити ID відповідних одиниць.
            2. Формула (formula) базується на значенні 'x' (наприклад x * 10).
            3. Зворотня формула (reverse_formula) має розраховувати зворотнє перетворення.
            4. Усі формули повинні бути зручними для Python (ступінь `**`, замість `^`).
            
            Приклад конверсії:
            Гемоглобін: г/дл → мг/мл
            Одиниця вимірювання: грами на децилітр (г/дл) та міліграми на мілілітр (мг/мл).
            Формула конверсії:
            мг/мл=г/дл×10
            Зворотна формула:
            г/дл=мг/мл/10
            Пояснення: 1 грам = 1000 міліграмів, і оскільки 1 децилітр = 100 мілілітрів, множимо на 10.
            
            Приклад відповіді:
                "unit_from_id": 1,
                "unit_to_id": 2,
                "formula": "x * 10",
                "reverse_formula": "x / 10"
            """

            # Отримуємо відповідь від LLM
            llm_response = get_llm_response(prompt, Conversions)

            try:
                    existing_conversion = db.query(UnitConversion).filter(
                        UnitConversion.from_unit_id == llm_response['unit_from_id'],
                        UnitConversion.to_unit_id == llm_response['unit_to_id'],
                        UnitConversion.standard_name_id == standard_name_id
                    ).first()

                    if not existing_conversion:
                        new_conversion = UnitConversion(
                            from_unit_id=llm_response['unit_from_id'],
                            to_unit_id=llm_response['unit_to_id'],
                            formula=llm_response['formula'],
                            standard_name_id=standard_name_id
                        )
                        db.add(new_conversion)
            except Exception as e:
                print(f"Помилка під час парсингу LLM-відповіді: {e}")

        # Зберігаємо зміни в базі даних
        db.commit()
        print("Усі конверсії успішно збережені в базі даних.")

        return 'finish'

    except Exception as e:
        print(f"Помилка під час генерації пар: {e}")
        return []

    finally:
        db.close()
