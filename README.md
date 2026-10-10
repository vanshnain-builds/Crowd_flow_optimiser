# Crowd-o-holic

Crowd flow optimisation dashboard and simulation platform with a React frontend and FastAPI backend.

## Projects

- `frontend/` — Vite + React + TypeScript UI
- `backend/` — FastAPI backend and simulation API
- `start-backend.bat` — Windows helper script to start the backend

## Getting started

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python -m uvicorn app.main:app --reload
```

If you use uv, you can also run:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

## Notes

This repository was prepared for GitHub upload and is ready to be pushed to your remote repository.
