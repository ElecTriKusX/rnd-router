# Backend R&D Router

## Запуск

```powershell
uv sync
uv run pytest
uv run uvicorn --app-dir src api.app:app --reload
```

Swagger будет доступен по адресу `http://127.0.0.1:8000/docs`.

## Подготовка данных

После добавления Markdown-профилей в `../data/profiles_raw/` выполните:

```powershell
uv run python -m infrastructure.profile_parser
uv run python -m infrastructure.index_builder
```

Первый скрипт создаёт `../data/profiles.json`, второй — `../data/index.parquet`. Для сборки индекса нужны рабочие переменные Yandex из `.env`.

## API

- `GET /health` — проверка доступности API;
- `POST /api/v1/matches` — декомпозиция запроса, поиск и rerank кандидатов;
- `POST /api/v1/email-drafts` — создание письма для выбранного кандидата.
