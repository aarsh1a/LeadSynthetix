"""
End-to-end integration test: PDF upload → extraction → agents → decision.

Uses the real pipeline with no mocks.
Runs standalone — no external server or Postgres required.
Uses FastAPI TestClient + in-memory SQLite.

Usage:
  cd backend
  source .venv/bin/activate
  python -m tests.test_upload_pipeline                      # uses built-in sample
  python -m tests.test_upload_pipeline /path/to/real.pdf    # uses your PDF
"""

import json
import os
import sys
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Force DATABASE_URL to SQLite BEFORE any app code is imported.
#    This ensures app.config.get_settings() picks up the override.
# ---------------------------------------------------------------------------
os.environ["DATABASE_URL"] = "sqlite:///file::memory:?cache=shared&uri=true"

# ---------------------------------------------------------------------------
# 2. SQLite compatibility shims for PostgreSQL-specific column types.
#    Must be registered BEFORE any models call metadata.create_all().
# ---------------------------------------------------------------------------
from sqlalchemy import event
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB


@compiles(PG_UUID, "sqlite")
def _compile_pg_uuid_sqlite(type_, compiler, **kw):
    return "CHAR(36)"


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


# ---------------------------------------------------------------------------
# 3. Now safe to import the app. The database module will create an engine
#    pointing at our in-memory SQLite thanks to the env override.
# ---------------------------------------------------------------------------
from app.models.base import Base
from app.models.database import engine, get_db, SessionLocal
from app.main import app as fastapi_app

# Create all tables in the in-memory SQLite database
Base.metadata.create_all(bind=engine)

# Enable SQLite foreign-key enforcement
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# ---------------------------------------------------------------------------
# TestClient (no live server needed)
# ---------------------------------------------------------------------------
from starlette.testclient import TestClient

client = TestClient(fastapi_app)

DIVIDER = "─" * 60


def create_sample_pdf() -> Path:
    """Create a minimal PDF with embedded financial data for testing."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("✗ PyMuPDF not installed. Install with: pip install pymupdf")
        sys.exit(1)

    content = textwrap.dedent("""\
        FINANCIAL SUMMARY — Apex Dynamics Ltd.

        Industry: Advanced Manufacturing
        Fiscal Year: 2025

        Revenue: $18.5M
        Total Debt: $6.2M
        DSCR: 1.28

        The company has pledged assets as collateral against the
        senior credit facility.

        Board and directors have been fully vetted.
        All regulatory checks passed.
    """)

    path = Path(__file__).parent / "_sample_test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), content, fontsize=11)
    doc.save(str(path))
    doc.close()
    return path


def upload_pdf(pdf_path: Path) -> dict:
    """POST the PDF to the upload endpoint via TestClient."""
    print(f"\n📄 Uploading: {pdf_path.name}")
    print(f"   Endpoint:  POST /api/ingest/upload  (TestClient)")
    print(DIVIDER)

    with open(pdf_path, "rb") as f:
        resp = client.post(
            "/api/ingest/upload",
            files={"file": (pdf_path.name, f, "application/pdf")},
        )

    if resp.status_code != 200:
        print(f"✗ Upload failed (HTTP {resp.status_code})")
        print(resp.text[:1000])
        sys.exit(1)

    return resp.json()


def print_results(data: dict) -> None:
    """Pretty-print the pipeline output."""
    print("\n✓ Pipeline complete\n")

    # ── Loan summary ──
    print(DIVIDER)
    print("LOAN APPLICATION")
    print(DIVIDER)
    print(f"  Loan ID          : {data['loan_id']}")
    print(f"  Company           : {data['company_name']}")
    print(f"  Workflow State    : {data['workflow_state']}")
    print()

    # ── Extracted financials ──
    fin = data.get("extracted_financials") or {}
    print(DIVIDER)
    print("EXTRACTED FINANCIALS")
    print(DIVIDER)
    print(f"  Revenue           : {fin.get('revenue')}")
    print(f"  Debt              : {fin.get('debt')}")
    print(f"  DSCR              : {fin.get('dscr')}")
    print(f"  Collateral        : {fin.get('collateral_present')}")
    print(f"  Compliance Kw     : {fin.get('compliance_keywords', [])}")
    print()

    # ── Agent memos ──
    memos = data.get("agent_memos", [])
    print(DIVIDER)
    print("AGENT SCORES & MEMOS")
    print(DIVIDER)
    for m in memos:
        agent = m["agent_type"]
        score = m.get("risk_score", "—")
        content = m["content"][:120]
        print(f"  [{agent:>12}]  score={score}")
        print(f"                    {content}")
        print()

    # ── Decision ──
    print(DIVIDER)
    print("FINAL DECISION")
    print(DIVIDER)
    print(f"  Status            : {data['status']}")
    print(f"  Final Score       : {data['final_score']}")
    print(f"  Confidence Score  : {data['confidence_score']}")
    print(f"  Compliance Flag   : {data['compliance_flag']}")
    print()

    # ── Raw JSON ──
    print(DIVIDER)
    print("RAW JSON")
    print(DIVIDER)
    print(json.dumps(data, indent=2, default=str))
    print()


def main():
    # Determine PDF path
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
        if not pdf_path.exists():
            print(f"✗ File not found: {pdf_path}")
            sys.exit(1)
    else:
        print("No PDF argument provided — generating a sample PDF …")
        pdf_path = create_sample_pdf()

    data = upload_pdf(pdf_path)
    print_results(data)

    loan_id = data["loan_id"]

    # ── Test GET /api/loans/ ──
    print(DIVIDER)
    print("TEST: GET /api/loans/")
    print(DIVIDER)
    resp = client.get("/api/loans/")
    assert resp.status_code == 200, f"GET /api/loans/ failed: {resp.status_code}"
    loans_list = resp.json()
    assert isinstance(loans_list, list) and len(loans_list) >= 1
    assert any(l["id"] == loan_id for l in loans_list)
    print(f"  ✓ Returned {len(loans_list)} loan(s), includes uploaded loan")
    print()

    # ── Test GET /api/loans/:id ──
    print(DIVIDER)
    print("TEST: GET /api/loans/:id")
    print(DIVIDER)
    resp = client.get(f"/api/loans/{loan_id}")
    assert resp.status_code == 200, f"GET /api/loans/{{id}} failed: {resp.status_code}"
    loan_detail = resp.json()
    assert loan_detail["id"] == loan_id
    assert loan_detail["status"] in ("Approved", "Rejected", "Pending")
    assert "agent_memos" in loan_detail and len(loan_detail["agent_memos"]) >= 3
    print(f"  ✓ Loan detail returned with {len(loan_detail['agent_memos'])} memos")
    print()

    # ── Test POST /api/chat/ ──
    print(DIVIDER)
    print("TEST: POST /api/chat/")
    print(DIVIDER)
    resp = client.post(
        "/api/chat/",
        json={
            "loan_id": loan_id,
            "message": "Why was this loan approved or rejected?",
            "history": [],
        },
    )
    assert resp.status_code == 200, f"POST /api/chat/ failed: {resp.status_code}"
    chat_data = resp.json()
    assert "reply" in chat_data and len(chat_data["reply"]) > 0
    print(f"  ✓ Chat reply: {chat_data['reply'][:100]}...")
    print()

    # ── Test 404 for unknown loan ──
    print(DIVIDER)
    print("TEST: GET /api/loans/:id (404)")
    print(DIVIDER)
    resp = client.get("/api/loans/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    print("  ✓ Returns 404 for unknown loan")
    print()

    print("=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)

    # Cleanup generated sample
    sample = Path(__file__).parent / "_sample_test.pdf"
    if sample.exists() and pdf_path == sample:
        sample.unlink()


if __name__ == "__main__":
    main()
