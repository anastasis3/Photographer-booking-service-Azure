FROM python:3.11-slim

WORKDIR /app

COPY main.py .

# Устанавливаем все нужные зависимости, включая azure-servicebus
RUN pip install fastapi uvicorn azure-servicebus azure-storage-queue python-dotenv

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
