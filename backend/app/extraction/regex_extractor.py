"""Regex-based deterministic extraction."""

import re
from app.extraction.schemas import ExtractionResult

# Compliance keywords to search (case-insensitive)
COMPLIANCE_KEYWORDS = [
    "offshore",
    "grey list",
    "gray list",
    "aml",
    "anti-money laundering",
    "sanctions",
    "pep",
    "politically exposed",
]

# Collateral-related phrases
COLLATERAL_PATTERNS = [
    r"\bcollateral\b",
    r"\bpledged\s+assets\b",
    r"\bsecurity\s+interest\b",
    r"\bsecured\s+by\b",
    r"\bguarantee\b",
    r"\bguarantor\b",
]

# Numeric patterns - capture value and optional multiplier
# e.g. "Revenue: $12.5M", "Revenue $12.5 million", "12.5M"
_MONEY_SUFFIX = r"(?:\s*(million|m|mn|mm|billion|b|bn|k|thousand))?"
MONEY_PATTERN = re.compile(
    r"(?:revenue|sales|top\s*line)[:\s]*"
    r"(?:[\$\€\£]?\s*)?"
    r"([\d,]+(?:\.\d+)?)"
    + _MONEY_SUFFIX,
    re.IGNORECASE,
)
DEBT_PATTERN = re.compile(
    r"(?:total\s+)?(?:debt|liabilities|outstanding\s+debt)[:\s]*"
    r"(?:[\$\€\£]?\s*)?"
    r"([\d,]+(?:\.\d+)?)"
    + _MONEY_SUFFIX,
    re.IGNORECASE,
)
DSCR_PATTERN = re.compile(
    r"(?:dscr|debt\s+service\s+coverage\s+ratio)[:\s]*"
    r"([\d.]+)",
    re.IGNORECASE
)


def _parse_amount(s: str, multiplier: str | None) -> float:
    """Parse numeric string and apply multiplier (M, B, K)."""
    s = s.replace(",", "")
    try:
        val = float(s)
    except ValueError:
        return 0.0
    mult = (multiplier or "").lower()
    if mult in ("m", "mn", "mm", "million"):
        return val * 1_000_000
    if mult in ("b", "bn", "billion"):
        return val * 1_000_000_000
    if mult in ("k", "thousand"):
        return val * 1_000
    return val


def _extract_first_money(text: str, pattern: re.Pattern) -> float | None:
    """Extract first matching monetary value."""
    m = pattern.search(text)
    if not m:
        return None
    num_str = m.group(1)
    mult = m.group(2) if m.lastindex and m.lastindex >= 2 else None
    val = _parse_amount(num_str, mult)
    return val if val else None


def extract_with_regex(text: str) -> ExtractionResult:
    """Deterministic extraction using regex."""
    revenue = _extract_first_money(text, MONEY_PATTERN)
    debt = _extract_first_money(text, DEBT_PATTERN)
    dscr: float | None = None
    m = DSCR_PATTERN.search(text)
    if m:
        try:
            dscr = float(m.group(1))
        except ValueError:
            pass

    collateral_present = any(
        re.search(p, text, re.IGNORECASE) for p in COLLATERAL_PATTERNS
    )

    found_keywords: list[str] = []
    for kw in COMPLIANCE_KEYWORDS:
        if re.search(re.escape(kw), text, re.IGNORECASE):
            found_keywords.append(kw)

    return ExtractionResult(
        revenue=revenue,
        debt=debt,
        dscr=dscr,
        collateral_present=collateral_present,
        compliance_keywords=found_keywords,
    )
