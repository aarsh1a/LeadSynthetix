"""Decision Memo service - generates PDF with executive summary, memos, risk matrix, timeline."""

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from app.models.loan_application import LoanApplication
from app.services.risk_matrix_service import get_risk_matrix


def _escape(s: str) -> str:
    """Escape for ReportLab Paragraph (XML-like)."""
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _format_datetime(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _build_executive_summary(loan: LoanApplication) -> str:
    """Generate executive summary."""
    status = loan.status or "Pending"
    score = loan.final_score if loan.final_score is not None else "—"
    conf = loan.confidence_score if loan.confidence_score is not None else "—"
    parts = [
        f"This decision memo summarizes the lending assessment for {loan.company_name} ({loan.industry}). "
        f"Requested amount: ${loan.requested_amount:,.0f}. "
        f"Final status: {status}. Final score: {score}. Confidence: {conf}."
    ]
    return " ".join(parts)


def _build_compliance_notes(loan: LoanApplication) -> str:
    """Build compliance notes from agent memo and extracted data."""
    notes: list[str] = []
    financials = loan.extracted_financials or {}
    keywords = financials.get("compliance_keywords") or []
    if keywords:
        notes.append(f"Compliance keywords detected: {', '.join(keywords)}.")
    compliance_memo = next(
        (m for m in loan.agent_memos if m.agent_type == "Compliance"),
        None,
    )
    if compliance_memo:
        notes.append(compliance_memo.content[:500])
    if loan.compliance_flag:
        notes.append("Application flagged for compliance review.")
    return " ".join(notes) if notes else "No compliance issues identified."


def generate_decision_memo_pdf(loan: LoanApplication) -> bytes:
    """Generate a professional PDF decision memo."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    h2_style = ParagraphStyle(
        name="CustomH2",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=16,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        name="CustomBody",
        parent=styles["Normal"],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    small_style = ParagraphStyle(
        name="Small",
        parent=styles["Normal"],
        fontSize=9,
        spaceAfter=4,
    )

    flow: list[Any] = []

    # Title
    flow.append(Paragraph("LendSynthetix — Decision Memo", title_style))
    flow.append(Paragraph(f"Loan ID: {loan.id}", small_style))
    flow.append(Paragraph(f"Generated: {_format_datetime(datetime.utcnow())}", small_style))
    flow.append(Spacer(1, 0.25 * inch))

    # Executive Summary
    flow.append(Paragraph("Executive Summary", h2_style))
    flow.append(Paragraph(_escape(_build_executive_summary(loan)), body_style))
    flow.append(Spacer(1, 0.2 * inch))

    # Key metrics table
    flow.append(Paragraph("Key Metrics", h2_style))
    metrics_data = [
        ["Company", _escape(loan.company_name)],
        ["Industry", loan.industry],
        ["Requested Amount", f"${loan.requested_amount:,.0f}"],
        ["Status", loan.status or "—"],
        ["Final Score", str(loan.final_score) if loan.final_score is not None else "—"],
        ["Confidence Score", str(loan.confidence_score) if loan.confidence_score is not None else "—"],
        ["Workflow State", loan.workflow_state or "—"],
    ]
    t = Table(metrics_data, colWidths=[2 * inch, 4 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 0.3 * inch))

    # Agent Memos
    flow.append(Paragraph("Agent Memos", h2_style))
    order = {"Sales": 0, "Risk": 1, "Compliance": 2, "Moderator": 3}
    for memo in sorted(loan.agent_memos, key=lambda m: (order.get(m.agent_type, 9), m.created_at or datetime.min)):
        flow.append(Paragraph(f"<b>{memo.agent_type}</b> (Score: {memo.risk_score or '—'})", small_style))
        content_clean = _escape(memo.content or "")
        flow.append(Paragraph(content_clean[:2000] + ("..." if len(memo.content or "") > 2000 else ""), body_style))
        flow.append(Spacer(1, 0.1 * inch))
    flow.append(Spacer(1, 0.2 * inch))

    # Risk Matrix
    flow.append(Paragraph("Risk Matrix", h2_style))
    financials = loan.extracted_financials or {}
    risk = get_risk_matrix(financials)
    risk_data = [
        ["Category", "Score (1-10)", "Evidence"],
        ["Financial Risk", str(risk.financial_risk.score), "; ".join(risk.financial_risk.evidence[:2]) or "—"],
        ["Growth Strength", str(risk.growth_strength.score), "; ".join(risk.growth_strength.evidence[:2]) or "—"],
        ["Regulatory Risk", str(risk.regulatory_risk.score), "; ".join(risk.regulatory_risk.evidence[:2]) or "—"],
        ["Reputation Risk", str(risk.reputation_risk.score), "; ".join(risk.reputation_risk.evidence[:2]) or "—"],
    ]
    t2 = Table(risk_data, colWidths=[1.5 * inch, 1 * inch, 3.5 * inch])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
    ]))
    flow.append(t2)
    flow.append(Spacer(1, 0.3 * inch))

    # Compliance Notes
    flow.append(Paragraph("Compliance Notes", h2_style))
    flow.append(Paragraph(_escape(_build_compliance_notes(loan)), body_style))
    flow.append(Spacer(1, 0.3 * inch))

    # Timeline of Events
    flow.append(Paragraph("Timeline of Events", h2_style))
    logs = sorted(loan.audit_logs, key=lambda a: a.timestamp or datetime.min)
    if logs:
        timeline_data = [["Timestamp", "Event", "Details"]]
        for log in logs:
            ts = _format_datetime(log.timestamp)
            evt = log.event_type
            det = ""
            if log.details:
                det = ", ".join(f"{k}: {v}" for k, v in list(log.details.items())[:4])
            timeline_data.append([ts, evt, det[:60] + "..." if len(det) > 60 else det])
        t3 = Table(timeline_data, colWidths=[1.5 * inch, 1.8 * inch, 2.7 * inch])
        t3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        flow.append(t3)
    else:
        flow.append(Paragraph("No audit events recorded.", body_style))

    doc.build(flow)
    return buffer.getvalue()
