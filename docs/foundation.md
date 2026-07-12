# Foundation: модели, pytest и FastAPI

## Согласованная структура

```text
backend/
  src/
    domain/           # Pydantic-модели и инварианты
    services/         # сценарии подбора, rerank и письма
    infrastructure/   # Yandex, parquet, профили и промпты
    api/              # FastAPI-роуты
    legacy/           # исходный код до миграции
  tests/
frontend/             # будущий React + TypeScript
prompts/              # версии промптов
data/                 # локальные данные или объектное хранилище
```

`legacy/` — не второй backend. Это безопасно сохранённый исходный код, который будет переноситься по частям: с тестами и без одновременного изменения поведения. После миграции каталог исчезнет.

## Логика единых моделей

Одна сущность должна иметь одно значение во всём продукте. Поэтому `domain.models.Profile` — единственная модель исследователя: парсер создаёт её, поиск возвращает её, API сериализует её, а интерфейс отображает её. Поле `email` находится у профиля, а не появляется только при создании письма.

`ResearchRequest` — это входящий запрос клиента. Он намеренно отделён от `Grant`: грант — историческая запись в профиле, а не любое новое обращение. Это убирает прежнюю неоднозначность, когда UI передавал строку, а ML-функция ожидала `Grant`.

`CandidateMatch` соединяет две разные вещи: неизменяемый `Profile` и контекст подбора (`score`, `reasons`). Результаты сгруппированы в `SubtaskMatches`, так как один запрос может распадаться на несколько подзадач.

## Как читать тесты

Запуск:

```powershell
& C:\Users\elect\.local\bin\uv.exe run pytest
```

`backend/tests/test_models.py` — unit-тест: создаём модель и проверяем её инвариант. `pytest.raises(ValidationError)` убеждается, что score больше 1 не пересекает границу доменной модели. JSON в `backend/tests/fixtures/` — небольшие versioned тестовые данные; их формат проверяет та же каноническая `Profile`.

`backend/tests/test_api.py` следует схеме Arrange-Act-Assert:

1. Arrange: pytest-fixture `configured_client` подменяет `get_matching_service` на `StubMatchingService` и затем очищает подмену.
2. Act: `TestClient` отправляет HTTP-запрос без запуска настоящего сервера.
3. Assert: тест проверяет HTTP-статус и важные поля JSON-контракта.

Stub заменяет внешний мир предсказуемым ответом. Поэтому тесты быстрые, бесплатные и не требуют `.env` или ключа Yandex.

## Как читать FastAPI

В `backend/src/api/app.py` модель `MatchCommand` описывает тело запроса, а FastAPI/Pydantic валидируют его до вызова endpoint. `response_model=MatchResponse` фиксирует ответ, который будет потреблять React.

`Depends(get_matching_service)` — точка подключения настоящей реализации. Сейчас она возвращает 503 только для валидного запроса: реальных `profiles.json` и индекса в репозитории нет. Когда они появятся, сюда подключится сервис, объединяющий `decompose`, `retrieve` и `rerank`; API и frontend-контракт менять не придётся.

Запуск API и Swagger-документации:

```powershell
& C:\Users\elect\.local\bin\uv.exe run uvicorn --app-dir backend/src api.app:app --reload
```

Откройте `http://127.0.0.1:8000/docs`. Для первой самостоятельной практики добавьте `GET /api/v1/profiles/{profile_id}`: сначала напишите тесты на успешный ответ и 404, затем endpoint.
