FROM python:3.11-slim

WORKDIR /app

COPY main.py .

# Установим зависимости
RUN pip install fastapi uvicorn httpx azure-servicebus azure-storage-queue python-dotenv

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
