# LendSynthetix

Production-ready full-stack lending analysis platform.

## Tech Stack

- **Backend:** FastAPI (Python 3.11)
- **Frontend:** Next.js 14 (App Router) + TypeScript
- **Styling:** Tailwind CSS
- **State:** Zustand
- **Database:** PostgreSQL (SQLAlchemy)
- **PDF:** PyMuPDF
- **LLM:** OpenAI (abstracted service layer)
- **Tasks:** FastAPI BackgroundTasks

## Project Structure

```
LendSynthetix/
├── backend/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── ingestion/
│       ├── extraction/
│       ├── agents/
│       ├── orchestration/
│       ├── scoring/
│       ├── compliance/
│       ├── audit/
│       ├── api/
│       │   └── routes/
│       ├── models/
│       └── services/
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── dashboard/
│   ├── components/
│   │   ├── Dashboard/
│   │   ├── DebateTimeline/
│   │   ├── RiskPanel/
│   │   ├── CompliancePanel/
│   │   ├── EvidenceDrawer/
│   │   ├── DecisionSummary/
│   │   └── UploadSection/
│   ├── stores/
│   ├── lib/
│   └── types/
└── .env.example
```

## Setup

1. Copy `.env.example` to `.env` and fill in values.
2. Backend: `cd backend && pip install -r requirements.txt`
3. Database: `alembic upgrade head` (from backend dir)
4. Frontend: `cd frontend && npm install`

## Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

## Test Scenarios

Run 4 automated synthetic loan scenarios (no DB or LLM required):

```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=. python -m tests.run_scenarios
```

Or with pytest:

```bash
cd backend
pytest tests/test_scenarios.py -v -s
```
