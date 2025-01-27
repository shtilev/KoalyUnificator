import requests
from bs4 import BeautifulSoup
import re
import json

base_url = 'https://unitslab.com/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

response = requests.get(base_url, headers=headers)
if response.status_code == 200:
    html_content = response.text
else:
    print(f"Не вдалося отримати сторінку, код помилки: {response.status_code}")
    exit()

soup = BeautifulSoup(html_content, 'html.parser')

ul_blockanaliz = soup.find('ul', class_='blockanaliz')

if not ul_blockanaliz:
    print("Не знайдено ul з класом 'blockanaliz'")
    exit()

li_items = ul_blockanaliz.find_all('li')

href_list = []
for li in li_items:
    a_tag = li.find('a')
    if a_tag and 'href' in a_tag.attrs:
        href = a_tag['href']
        # Перевірка, чи посилання вже містить '/uk/'
        if '/uk/' in href:
            full_url = base_url.rstrip('/') + href
        else:
            full_url = base_url.rstrip('/') + '/uk' + href
        href_list.append(full_url)


results = []

for href in href_list:
    print(f"Обробляємо сторінку: {href}")
    sub_response = requests.get(href, headers=headers)
    if sub_response.status_code == 200:
        sub_html_content = sub_response.text
        sub_soup = BeautifulSoup(sub_html_content, 'html.parser')

        page_header = sub_soup.find('h1', class_='page-header')
        if page_header:
            span = page_header.find('span')
            title = span.text.strip() if span else "Без назви"
        else:
            title = "Без назви"

        factor_match = re.search(r'function FACTOR\s*\(\)\s*{(.*?)}', sub_html_content, re.DOTALL)
        if factor_match:
            factor_code = factor_match.group(1).strip()

            units_dict = {}
            lines = factor_code.splitlines()
            for line in lines:
                if line.strip().startswith("//"):  # Пропускаємо закоментовані рядки
                    continue
                match = re.search(r'this\.mass\d+\s*=\s*([\d\.e\-]+)\s*//\s*(.+)', line)
                if match:
                    value = float(match.group(1))  # Конвертуємо значення у float
                    unit = match.group(2).strip()  # Витягуємо юніт
                    units_dict[unit] = value

            # Генеруємо пари одиниць і формули
            calculator = []
            unit_keys = list(units_dict.keys())
            for i in range(len(unit_keys)):
                for j in range(len(unit_keys)):
                    if i != j:  # Уникаємо пар однакових одиниць
                        from_unit = unit_keys[i]
                        to_unit = unit_keys[j]
                        formula = f"(x * {units_dict[from_unit]}) / {units_dict[to_unit]}"
                        calculator.append({
                            "from": from_unit,
                            "to": to_unit,
                            "formula": formula
                        })

            # Додаємо результат у список
            results.append({
                "analysis-name": title,
                "calculator": calculator
            })
        else:
            print(f"Метод FACTOR не знайдено на сторінці {href}")
    else:
        print(f"Не вдалося отримати сторінку: {href}, код помилки: {sub_response.status_code}")

# Збереження результатів у JSON-файл
output_file = 'results.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print(f"\nРезультати збережено у файл: {output_file}")
