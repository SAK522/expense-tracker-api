# Expense Tracker REST API

A secured REST API for tracking personal income and expenses. Built with **FastAPI**, **PostgreSQL**, and **JWT authentication**. Each user can only see and change their own data.

- **Web app (no coding needed):** https://expense-tracker-api-9rcd.onrender.com
- **Interactive API docs (for developers):** https://expense-tracker-api-9rcd.onrender.com/docs

> Free hosting: the first request after 15 idle minutes can take up to a minute while the server wakes up.

## Features

- **A web dashboard for non-technical users** at `/`: a one-click demo month, income / spending / balance cards, spending by category, an add-and-edit form and the full transaction list. Amounts are shown in rupees with Indian digit grouping. A private guest account is created automatically, with no sign-up.
- Sign up and log in with email + password (passwords hashed with bcrypt)
- JWT bearer-token authentication on every protected route
- Create, read, update and delete income/expense transactions
- Filter transactions by month, category and type, with pagination
- Summary endpoint: total income, total expense and balance for any period
- Per-user data isolation: other users' records return `404`, as if they don't exist
- Input validation (positive amounts, valid dates, valid emails) via Pydantic
- 26 automated tests (pytest) covering auth, CRUD, filters, summary and ownership

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI |
| Database | PostgreSQL (SQLite for local dev) via SQLAlchemy 2 |
| Auth | JWT (PyJWT) + bcrypt password hashing |
| Validation | Pydantic v2 |
| Tests | pytest + FastAPI TestClient |
| Deploy | Render (Blueprint) or Docker |

## API endpoints

| Method | Path | Purpose | Auth |
|---|---|---|---|
| POST | `/auth/signup` | Create an account | No |
| POST | `/auth/login` | Get a JWT token | No |
| GET | `/auth/me` | Show the logged-in account | Yes |
| GET | `/transactions` | List my transactions (`?month=YYYY-MM&category=&type=&limit=&offset=`) | Yes |
| POST | `/transactions` | Add a transaction | Yes |
| GET | `/transactions/{id}` | Get one of my transactions | Yes |
| PUT | `/transactions/{id}` | Update my transaction (send only changed fields) | Yes |
| DELETE | `/transactions/{id}` | Delete my transaction | Yes |
| GET | `/summary` | Totals for a period (`?month=YYYY-MM` or `?start_date=&end_date=`) | Yes |
| GET | `/health` | Health check | No |

## Data model

- **users**: id, email (unique), password_hash, created_at
- **transactions**: id, user_id → users.id, amount (NUMERIC 12,2), type (`income`/`expense`), category, note, date, created_at

Every transaction query filters by the logged-in user's id, which is what keeps data separate.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs. Locally it uses a SQLite file (`expense.db`), so you don't need to install PostgreSQL.

## Run the tests

```bash
pytest
```

Tests run against a throwaway in-memory database, so they never touch your data.

## Example requests

```bash
BASE=http://127.0.0.1:8000

# 1. Sign up
curl -X POST $BASE/auth/signup -H "Content-Type: application/json" \
  -d '{"email":"priya@example.com","password":"secret123"}'

# 2. Log in (form fields: username = email)
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -d "username=priya@example.com&password=secret123" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 3. Add an expense
curl -X POST $BASE/transactions -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"amount":"450.00","type":"expense","category":"Food","note":"Lunch","date":"2026-11-10"}'

# 4. List this month's expenses
curl "$BASE/transactions?month=2026-11&type=expense" -H "Authorization: Bearer $TOKEN"

# 5. Monthly summary
curl "$BASE/summary?month=2026-11" -H "Authorization: Bearer $TOKEN"
```

Example summary response:

```json
{
  "start_date": "2026-11-01",
  "end_date": "2026-11-30",
  "total_income": "50000.00",
  "total_expense": "1650.50",
  "balance": "48349.50",
  "transaction_count": 3
}
```

Money values are returned as strings (e.g. `"450.00"`) so they never lose precision the way floating-point numbers can.

## Deploy to Render

1. Push this project to a GitHub repository.
2. In Render: **New → Blueprint**, then select the repository. `render.yaml` creates the web service and a free PostgreSQL database named `portfolio-db`, and connects them.
3. Wait for the build, then open `https://<your-service>.onrender.com/docs`.

`JWT_SECRET` is generated automatically and `DATABASE_URL` is filled in from the database. The app keeps its tables in its own PostgreSQL schema (`DATABASE_SCHEMA=expense`), so other projects can share the same free database without their tables mixing. Free services sleep after 15 minutes without traffic, and free Render PostgreSQL databases expire 30 days after creation, so check Render's current free-tier terms.

**Alternative (Docker / Railway):** the included `Dockerfile` runs anywhere. Set `DATABASE_URL`, `JWT_SECRET` and optionally `DATABASE_SCHEMA` as environment variables.

## Project structure

```
app/
  main.py              # app entry point, registers routers, serves the web app at /
  web/index.html       # the web dashboard (one self-contained page, no build step)
  config.py            # settings from environment variables
  database.py          # engine, sessions, get_db dependency
  models.py            # SQLAlchemy tables (users, transactions)
  schemas.py           # Pydantic request/response shapes
  security.py          # bcrypt hashing + JWT create/verify
  deps.py              # get_current_user auth guard
  filters.py           # shared month/date-range helper
  routers/
    auth.py            # /auth/signup, /auth/login, /auth/me
    transactions.py    # CRUD + filters
    summary.py         # /summary totals
tests/                 # pytest suite
render.yaml            # Render Blueprint (web service + Postgres)
Dockerfile             # container build
```

## Future work

- Database migrations with Alembic
- Refresh tokens and logout / token revocation
- Rate limiting on login
- Multi-currency support and budgets per category
- A front-end (web or mobile) on top of this API
