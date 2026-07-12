# R&D Router

Project for matching researchers to incoming R&D requests and drafting personalised invitations.

## Foundation

The foundation backend lives in `backend/src/`:

- `domain/models.py` contains shared data contracts;
- `services/` contains matching, reranking, and email-drafting use cases;
- `infrastructure/` contains Yandex, index, profile, and prompt adapters;
- `api/` contains the FastAPI boundary for the future React client.

`frontend/` is reserved for the future React + TypeScript client. The existing Streamlit prototype will be kept separately as legacy code until it is replaced.

## Commands

```powershell
& C:\Users\elect\.local\bin\uv.exe run pytest
& C:\Users\elect\.local\bin\uv.exe run uvicorn --app-dir backend/src api.app:app --reload
```

See [docs/foundation.md](docs/foundation.md) for the model rationale and a walkthrough of pytest and FastAPI.
