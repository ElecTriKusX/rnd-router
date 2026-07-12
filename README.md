# R&D Router

Project for matching researchers to incoming R&D requests and drafting personalised invitations.

## Foundation

The foundation backend lives in `backend/src/`:

- `domain/models.py` contains shared data contracts;
- `services/` contains matching, reranking, and email-drafting use cases;
- `infrastructure/` contains Yandex, index, profile, and prompt adapters;
- `api/` contains the FastAPI boundary for the future React client.

`frontend/` is reserved for the future React + TypeScript client. The existing Streamlit prototype will be kept separately as legacy code until it is replaced.

## Команды backend

```powershell
cd backend
uv run pytest
uv run uvicorn --app-dir src api.app:app --reload
```

Подробности по backend: [backend/README.md](backend/README.md).
