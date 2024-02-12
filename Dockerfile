# Базовый образ с Python
FROM python:3.9-slim

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Создание и выбор рабочей директории внутри контейнера
WORKDIR /app

# Копирование файла зависимостей и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование содержимого текущей директории в рабочую директорию контейнера
COPY . .

# Команда для запуска приложения
CMD ["python", "main.py"]
