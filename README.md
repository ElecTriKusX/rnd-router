# R&D Router

R&D Router подбирает исследователей под входящие R&D-запросы, разбивает запрос на подзадачи, ранжирует кандидатов по их портфолио для конкретной подзадачи и готовит персональные письма-приглашения. Веб-интерфейс работает с FastAPI и Yandex AI Studio.

## Быстрый запуск в Docker

Нужен Docker с плагином Compose. Создайте файл с настройками Yandex AI Studio и запустите приложение:

```powershell
Copy-Item .env.example .env
# Заполните LLM_FOLDER_ID и LLM_API_KEY в .env
docker compose up --build -d
```

Контейнер API собирается из `python:3.12-slim` и устанавливает зависимости через `pip`.

После запуска интерфейс доступен по адресу <http://localhost:8080>, API — по адресу <http://localhost:8080/api/v1>, а Swagger — по адресу <http://localhost:8080/docs>.

Проверить состояние контейнеров и остановить приложение:

```powershell
docker compose ps
docker compose down
```

API не публикуется отдельным портом: к нему обращается только контейнер веб-интерфейса. Логи доступны командой `docker compose logs -f`.

## Настройка

Переменные окружения задаются в корневом `.env`; пример приведён в `.env.example`.

| Переменная | Назначение |
| --- | --- |
| `LLM_FOLDER_ID` | Идентификатор каталога Yandex Cloud. |
| `LLM_API_KEY` | API-ключ для Yandex AI Studio. |
| `LLM_CHAT_MODEL` | Модель для декомпозиции запросов и писем. |
| `LLM_EMBEDDING_MODEL` | Базовое имя модели эмбеддингов. |
| `LLM_COMPLETION_TIMEOUT` | Тайм-аут запросов к модели, в секундах. |
| `LLM_EMBEDDING_TIMEOUT` | Тайм-аут запросов эмбеддингов, в секундах. |

Файл `.env` не попадает в образ и не должен добавляться в Git.

## Данные исследователей

Для работы API при сборке образа нужны `data/profiles.json` и `data/index.parquet`. Они уже есть в рабочем проекте, но исключены из Git, так как могут содержать персональные данные.

Если исходные профили Markdown изменились, пересоберите данные локально, затем пересоберите контейнеры:

```powershell
cd backend
uv sync
uv run python -m infrastructure.profile_parser
uv run python -m infrastructure.index_builder
cd ..
docker compose up --build -d
```

Скрипт парсинга читает `data/profiles_raw/` и создаёт `data/profiles.json`; построение индекса создаёт `data/index.parquet` и требует заполненного `.env`.

## Разработка без Docker

Для backend нужен Python 3.10+; ниже используется [uv](https://docs.astral.sh/uv/) как удобный менеджер зависимостей. Он не обязателен: для обычного запуска API можно создать виртуальное окружение и установить `backend/requirements.txt` через `pip`. Для frontend нужен актуальный Node.js.

```powershell
# Терминал 1: API
cd backend
uv sync
uv run uvicorn --app-dir src api.app:app --reload

# Терминал 2: веб-интерфейс
cd frontend
npm ci
npm run dev
```

В режиме разработки Vite доступен по адресу <http://localhost:5173> и проксирует запросы API на `localhost:8000`.

## Тесты

```powershell
cd backend
uv run pytest

cd ../frontend
npm run build
```

## Структура проекта

- `backend/src/domain` — модели предметной области;
- `backend/src/services` — поиск, ранжирование и подготовка писем;
- `backend/src/infrastructure` — Yandex AI Studio, профили и векторный индекс;
- `backend/src/api` — HTTP API FastAPI;
- `frontend/src` — React-интерфейс;
- `data` — исходные профили и runtime-данные;
