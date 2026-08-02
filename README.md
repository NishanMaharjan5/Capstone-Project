# Smart Receipt Analyzer

OCR-based expense tracking: snap or manually enter receipts, track spending against budgets, and follow spending on trips — all in one app.

## Features

- **Receipt capture** — upload a photo and the app extracts vendor, date, total, and line items via OCR, or enter a receipt manually. Either way, you review and correct the extracted details before saving.
- **Dashboard** — recent receipts and at-a-glance spending insights.
- **History** — full searchable receipt history.
- **Analytics** — spending trends over time, category breakdown, day-of-week patterns, and vendor comparisons, all as interactive charts.
- **Budget management** — set an overall monthly budget, divide it across categories, see budget-vs-actual at a glance, and get decision-support suggestions when a category is trending over budget.
- **Trip tracker** — start a named trip with an optional overall and per-category budget, tag receipts to it as you go, and keep a full permanent summary (cumulative spend, day-by-day drill-down, category and vendor breakdowns) after the trip ends. Ended trips can be deleted with password confirmation.
- **Auth** — email/password with JWT sessions, Google sign-in, and forgot-password via emailed one-time code.

## Tech stack

**Backend** — FastAPI, Motor (async MongoDB driver), EasyOCR + OpenCV for receipt extraction, Plotly for chart generation, Pydantic, python-jose for JWT, passlib/bcrypt for password hashing.

**Frontend** — React 19 + Vite, React Router, react-plotly.js. Plain CSS, no framework.

**Database** — MongoDB.

## Project structure

```
backend/
  app/
    routers/     FastAPI endpoints (auth, receipts, budgets, trips)
    services/    Pure calculation/business logic — no DB access, called by routers
    db/          MongoDB connection and collections
    ocr/         Receipt image extraction pipeline
  main.py        App entrypoint, also serves the built frontend

frontend/
  src/
    pages/       One file per route (Dashboard, History, Analytics, Budgets, Trips, ...)
    components/  Shared UI pieces and charts
    api/         Thin fetch wrappers, one file per feature
    index.css    All styling lives here
```

## Running it locally

**Prerequisites:** Python 3.12+, Node 18.19+ (or 20+), a local MongoDB instance (or an Atlas connection string).

**macOS / Linux**

```bash
git clone https://github.com/NishanMaharjan5/Capstone-Project.git receipt-analyzer
cd receipt-analyzer

# Backend
cd backend
cp .env.example .env   # fill in values — see table below
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
cp .env.example .env
npm install
npm run dev
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/NishanMaharjan5/Capstone-Project.git receipt-analyzer
cd receipt-analyzer

# Backend
cd backend
copy .env.example .env   # fill in values — see table below
python -m venv venv      # if "python" isn't recognized, try "py" instead
.\venv\Scripts\Activate.ps1
# If that's blocked with a script-execution error, run this once then retry:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
copy .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`, register an account, and start using it.

## Running with Docker

No Python/Node/venv setup needed — just Docker Desktop installed and running.

```bash
cp backend/.env.example backend/.env   # fill in values — see table below
docker compose up --build
```

Then open:
- `http://localhost:5173` — frontend
- `http://localhost:8000` — backend

Both containers hot-reload on code changes, so you can edit files normally without rebuilding. The first run downloads PyTorch/EasyOCR and its OCR models, so it's slow (several minutes) — subsequent runs are much faster.

## Environment variables

**`backend/.env`**

| Variable | Required? | Notes |
|---|---|---|
| `MONGODB_URL` | Yes | e.g. `mongodb://localhost:27017` for a local instance |
| `DATABASE_NAME` | Yes | e.g. `receipt_analyzer` |
| `SECRET_KEY` | Yes | Signs JWTs — generate your own with `python3 -c "import secrets; print(secrets.token_hex(32))"`. The app refuses to start without this set. |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Only for Google sign-in | Leave as placeholders to skip that login option |
| `MAIL_EMAIL` / `MAIL_PASSWORD` | Only for forgot-password OTP emails | Leave blank to skip that flow |

**`frontend/.env`**

| Variable | Required? | Notes |
|---|---|---|
| `VITE_API_BASE_URL` | Yes | Defaults to `http://localhost:8000`, correct for local dev |
| `VITE_GOOGLE_CLIENT_ID` | Only for Google sign-in | Same client ID as the backend's |

## Screenshots

_TODO: add screenshots of the dashboard, analytics, budgets, and trip summary pages._
