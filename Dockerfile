# Використовуємо базовий образ Python
FROM python:3.11-slim

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо файли проєкту до контейнера
COPY . /app

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# Відкриваємо порт 9000
EXPOSE 9000

# Команда для запуску додатка
CMD ["uvicorn", "ui.server:app", "--host", "0.0.0.0", "--port", "9000"]
