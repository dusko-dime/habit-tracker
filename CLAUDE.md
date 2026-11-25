# Habit Tracker

Minimal habit tracker monorepo: FastAPI backend + React frontend. Keep it minimal — no features or dependencies beyond what's asked.

## Structure

```
backend/                 Python 3.13, uv, src layout
  src/backend/main.py    FastAPI app: models, DB engine, routes (all in one file)
  tests/test_api.py      pytest + TestClient
  habits.db              SQLite file, created on app startup (gitignored)
frontend/                React + Vite + TypeScript
  src/App.tsx            Whole UI: list habits, add form, "Done today" button
  src/App.test.tsx       Component test, fetch mocked
  src/setupTests.ts      Loads @testing-library/jest-dom matchers
  vite.config.ts         Dev proxy /api -> http://localhost:8000, Vitest config
```

## API

All routes are under `/api` (via `APIRouter(prefix="/api")`).

- `GET /api/habits` — list habits, each with computed `done_today: bool`
- `POST /api/habits` `{name}` — create (201); empty name → 422
- `POST /api/habits/{id}/check` — mark today done; idempotent; unknown id → 404

Models: `Habit(id, name, created_at)`, `HabitCheck(id, habit_id, date)`. Tables are created with `SQLModel.metadata.create_all` in the app lifespan — there are no migrations, so model changes need `habits.db` deleted.

## Commands

Backend (run in `backend/`):

```
uv run uvicorn backend.main:app --reload   # dev server on :8000
uv run ruff check .
uv run pytest
```

Frontend (run in `frontend/`):

```
npm run dev            # Vite on :5173, proxies /api to :8000
npm run lint
npm test -- --run      # plain `npm test` starts watch mode
npm run build          # tsc -b && vite build
```

The shell is PowerShell 5.1: chain commands with `;` or run them separately, not `&&`.

**Before calling a change done, run all checks:** ruff + pytest in `backend/`, lint + test + build in `frontend/`.

## Dependencies

Do not add dependencies without asking. Installed:

- Backend runtime: `fastapi`, `sqlmodel`, `uvicorn[standard]`
- Backend dev: `pytest`, `httpx` (for TestClient), `ruff`
- Frontend runtime: `react`, `react-dom` (v19)
- Frontend dev: `vite` (v8), `@vitejs/plugin-react`, `typescript` (v6), `vitest` (v5), `jsdom`, `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`, `eslint` + `typescript-eslint` + react-hooks/react-refresh plugins, `prettier`

## Testing conventions

- Backend: tests override `get_session` with an in-memory SQLite engine (`sqlite://` + `StaticPool`). Create `TestClient(app)` **without** a `with` block so the lifespan doesn't run and `habits.db` isn't created.
- Use `session.exec(select(...))`, not `session.query(...)` (deprecated in SQLModel).
- Frontend: mock fetch with `vi.stubGlobal('fetch', ...)` and `vi.unstubAllGlobals()` in `afterEach`. Import test APIs explicitly from `vitest` (globals are off).
