"""Risk Matrix - deterministic category scoring with evidence."""

from typing import Any

from app.scoring.schemas import RiskMatrixResult, CategoryScore


# Regulatory/Reputation keyword weights (deterministic)
REGULATORY_WEIGHTS: dict[str, int] = {
    "offshore": 3,
    "grey list": 2,
    "gray list": 2,
    "aml": 2,
    "anti-money laundering": 2,
    "sanctions": 2,
    "pep": 2,
    "politically exposed": 2,
}

REPUTATION_WEIGHTS: dict[str, int] = {
    "grey list": 3,
    "gray list": 3,
    "pep": 3,
    "politically exposed": 3,
    "offshore": 2,
    "aml": 1,
    "anti-money laundering": 1,
    "sanctions": 2,
}


def _dscr_to_risk(dscr: float | None) -> tuple[int, list[str]]:
    """Map DSCR to financial risk score (1-10, 10=highest) and evidence."""
    if dscr is None:
        return 9, ["DSCR not available"]
    if dscr <= 0:
        return 10, [f"DSCR {dscr} indicates inability to service debt"]
    if dscr < 0.5:
        return 9, [f"DSCR {dscr:.2f} severely below 1.0 threshold"]
    if dscr < 1.0:
        return 8, [f"DSCR {dscr:.2f} below 1.0 (cannot cover debt service)"]
    if dscr < 1.25:
        return 6, [f"DSCR {dscr:.2f} below 1.25 typical covenant"]
    if dscr < 1.5:
        return 4, [f"DSCR {dscr:.2f} adequate buffer"]
    return 2, [f"DSCR {dscr:.2f} strong debt service coverage"]


def _debt_revenue_risk(revenue: float | None, debt: float | None) -> tuple[int, list[str]]:
    """Debt/Revenue ratio contribution to financial risk."""
    if revenue is None or debt is None or revenue <= 0:
        return 0, []
    ratio = debt / revenue
    if ratio > 3:
        return 2, [f"Debt/Revenue {ratio:.1f}x indicates high leverage"]
    if ratio > 2:
        return 1, [f"Debt/Revenue {ratio:.1f}x moderate leverage"]
    if ratio > 1:
        return 0, [f"Debt/Revenue {ratio:.1f}x"]
    return -1, [f"Debt/Revenue {ratio:.1f}x conservative structure"]


def _financial_risk(financials: dict[str, Any]) -> CategoryScore:
    """Financial Risk 1-10 (10=highest). Deterministic from DSCR, debt, revenue, collateral."""
    dscr = financials.get("dscr")
    revenue = financials.get("revenue")
    debt = financials.get("debt")
    collateral = financials.get("collateral_present", False)

    score, evidence = _dscr_to_risk(dscr)
    adj, adj_ev = _debt_revenue_risk(revenue, debt)
    score = min(10, max(1, score + adj))
    evidence.extend(adj_ev)

    if collateral:
        score = max(1, score - 1)
        evidence.append("Collateral present reduces financial risk")

    if not evidence:
        evidence = ["Insufficient financial data for assessment"]

    return CategoryScore(score=score, evidence=evidence)


def _growth_strength(financials: dict[str, Any]) -> CategoryScore:
    """Growth Strength 1-10 (10=strongest). Deterministic from revenue, DSCR, collateral."""
    revenue = financials.get("revenue")
    dscr = financials.get("dscr")
    collateral = financials.get("collateral_present", False)

    evidence: list[str] = []
    score = 5  # baseline

    if revenue is not None and revenue > 0:
        if revenue >= 100_000_000:
            score = 9
            evidence.append(f"Revenue ${revenue/1e6:.0f}M indicates scale")
        elif revenue >= 10_000_000:
            score = 7
            evidence.append(f"Revenue ${revenue/1e6:.1f}M solid base")
        elif revenue >= 1_000_000:
            score = 6
            evidence.append(f"Revenue ${revenue/1e6:.2f}M")
        else:
            score = 4
            evidence.append(f"Revenue ${revenue:,.0f}")

    if dscr is not None:
        if dscr >= 1.5:
            score = min(10, score + 2)
            evidence.append(f"DSCR {dscr:.2f} suggests strong cash flow")
        elif dscr >= 1.25:
            score = min(10, score + 1)
            evidence.append(f"DSCR {dscr:.2f} supports growth capacity")
        elif dscr < 1.0:
            score = max(1, score - 2)
            evidence.append(f"DSCR {dscr:.2f} constrains growth capacity")

    if collateral:
        score = min(10, score + 1)
        evidence.append("Collateral supports financing capacity")

    if not evidence:
        evidence = ["Limited data for growth assessment"]

    return CategoryScore(score=min(10, max(1, score)), evidence=evidence)


def _match_keywords(user_keywords: list[str], weight_map: dict[str, int]) -> tuple[int, list[str]]:
    """Match user keywords against weight map. Returns (score delta, evidence)."""
    keywords = [str(k).lower().strip() for k in user_keywords]
    score = 1
    evidence: list[str] = []
    seen: set[str] = set()

    for user_kw in keywords:
        for known_kw, weight in weight_map.items():
            if known_kw in user_kw or user_kw in known_kw:
                if user_kw not in seen:
                    seen.add(user_kw)
                    score = min(10, score + weight)
                    evidence.append(f"Keyword detected: {user_kw}")
                break

    return score, evidence


def _regulatory_risk(compliance_keywords: list[str]) -> CategoryScore:
    """Regulatory Risk 1-10 (10=highest). Deterministic from compliance keywords."""
    score, evidence = _match_keywords(compliance_keywords or [], REGULATORY_WEIGHTS)
    if not evidence:
        evidence = ["No compliance keywords detected"]
    return CategoryScore(score=min(10, max(1, score)), evidence=evidence)


def _reputation_risk(compliance_keywords: list[str]) -> CategoryScore:
    """Reputation Risk 1-10 (10=highest). Deterministic from compliance keywords."""
    score, evidence = _match_keywords(compliance_keywords or [], REPUTATION_WEIGHTS)
    if not evidence:
        evidence = ["No reputation risk keywords detected"]
    return CategoryScore(score=min(10, max(1, score)), evidence=evidence)


def compute_risk_matrix(financials: dict[str, Any]) -> RiskMatrixResult:
    """
    Compute Risk Matrix from structured financials. Fully deterministic.
    """
    kw = financials.get("compliance_keywords") or []

    return RiskMatrixResult(
        financial_risk=_financial_risk(financials),
        growth_strength=_growth_strength(financials),
        regulatory_risk=_regulatory_risk(kw),
        reputation_risk=_reputation_risk(kw),
    )
