FROM python:3.12-slim

WORKDIR /app/backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dependencies are installed before source code to keep this layer cached
# between application changes. The container does not require uv.
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/src ./src
COPY data/profiles.json data/index.parquet /app/data/

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "--app-dir", "src", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
