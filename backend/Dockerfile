FROM python:3.12-slim

WORKDIR /app/backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/src ./src
RUN mkdir -p /app/data
COPY prompts /app/prompts

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "--app-dir", "src", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
