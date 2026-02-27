"""
Automated test scenarios for LendSynthetix.
Run: pytest tests/test_scenarios.py -v -s
Or: python -m tests.run_scenarios
"""

import uuid
from app.models.loan_application import LoanApplication
from app.agents.schemas import AgentResult
from app.orchestration.run_with_agents import run_workflow_with_results
from app.scoring.risk_matrix import compute_risk_matrix


# Case 1: High-growth tech startup
# High revenue growth, low collateral, moderate debt
# Expected: Sales strong, Risk skeptical, no compliance flag, Moderator required
CASE_1_FINANCIALS = {
    "revenue": 25_000_000,
    "debt": 8_000_000,
    "dscr": 1.1,
    "collateral_present": False,
    "compliance_keywords": [],
}

CASE_1_AGENTS = {
    "sales": AgentResult(memo="Strong growth trajectory. Recommend approval.", score=85, flags=[]),
    "risk": AgentResult(memo="DSCR weak, no collateral. High risk.", score=45, flags=["low DSCR"]),
    "compliance": AgentResult(memo="No compliance issues.", score=90, flags=[]),
    "moderator": AgentResult(memo="Moderator synthesis.", score=62, flags=[]),
}

# Case 2: Stable manufacturing, director on grey list
# Expected: Compliance veto, immediate rejection
CASE_2_FINANCIALS = {
    "revenue": 50_000_000,
    "debt": 12_000_000,
    "dscr": 1.4,
    "collateral_present": True,
    "compliance_keywords": ["grey list"],
}

CASE_2_AGENTS = {
    "sales": AgentResult(memo="Strong assets.", score=75, flags=[]),
    "risk": AgentResult(memo="Solid profile.", score=70, flags=[]),
    "compliance": AgentResult(memo="Director on grey list. Block.", score=15, flags=["grey list"]),
    "moderator": None,
}

# Case 3: Low revenue, high debt, weak cash flow
# Expected: Risk rejection, no compliance flag, final rejected
CASE_3_FINANCIALS = {
    "revenue": 2_000_000,
    "debt": 4_000_000,
    "dscr": 0.8,
    "collateral_present": False,
    "compliance_keywords": [],
}

CASE_3_AGENTS = {
    "sales": AgentResult(memo="Growth potential.", score=55, flags=[]),
    "risk": AgentResult(memo="Weak DSCR, high leverage. Reject.", score=25, flags=["weak DSCR"]),
    "compliance": AgentResult(memo="Clean.", score=85, flags=[]),
    "moderator": None,
}

# Case 4: Balanced mid-sized firm, healthy DSCR, no flags
# Expected: Approved without moderator
CASE_4_FINANCIALS = {
    "revenue": 15_000_000,
    "debt": 5_000_000,
    "dscr": 1.35,
    "collateral_present": True,
    "compliance_keywords": [],
}

CASE_4_AGENTS = {
    "sales": AgentResult(memo="Healthy profile. Approve.", score=78, flags=[]),
    "risk": AgentResult(memo="Strong DSCR, manageable leverage.", score=72, flags=[]),
    "compliance": AgentResult(memo="No flags.", score=88, flags=[]),
    "moderator": None,
}


def make_loan(
    name: str,
    industry: str,
    amount: float,
    financials: dict,
    compliance_flag: bool,
) -> LoanApplication:
    return LoanApplication(
        id=uuid.uuid4(),
        company_name=name,
        industry=industry,
        requested_amount=amount,
        extracted_financials=financials,
        status="Pending",
        workflow_state="INGESTED",
        compliance_flag=compliance_flag,
    )


def run_case(
    case_name: str,
    loan: LoanApplication,
    agents: dict,
) -> None:
    """Run one test case and print all outputs."""
    sales = agents["sales"]
    risk = agents["risk"]
    compliance = agents["compliance"]
    moderator = agents.get("moderator")

    _, output = run_workflow_with_results(
        loan,
        sales_result=sales,
        risk_result=risk,
        compliance_result=compliance,
        moderator_result=moderator,
    )

    risk_matrix = compute_risk_matrix(loan.extracted_financials or {})

    print("\n" + "=" * 60)
    print(f"  {case_name}")
    print("=" * 60)
    print(f"  Company: {loan.company_name}")
    print(f"  Agent Scores: Sales={output['agent_scores']['Sales']}, "
          f"Risk={output['agent_scores']['Risk']}, "
          f"Compliance={output['agent_scores']['Compliance']}")
    print(f"  Moderator Triggered: {output['moderator_triggered']}")
    if output.get("moderator_score") is not None:
        print(f"  Moderator Score: {output['moderator_score']}")
    print(f"  Compliance Flag: {output['compliance_flag']}")
    print(f"  Final Score: {output['final_score']}")
    print(f"  Final Decision: {output['final_decision']}")
    print(f"  Confidence Score: {output['confidence_score']}")
    print(f"  Auto Rejected: {output['auto_rejected']}")
    print("\n  Risk Matrix:")
    print(f"    Financial Risk: {risk_matrix.financial_risk.score}/10 - {risk_matrix.financial_risk.evidence}")
    print(f"    Growth Strength: {risk_matrix.growth_strength.score}/10 - {risk_matrix.growth_strength.evidence}")
    print(f"    Regulatory Risk: {risk_matrix.regulatory_risk.score}/10 - {risk_matrix.regulatory_risk.evidence}")
    print(f"    Reputation Risk: {risk_matrix.reputation_risk.score}/10 - {risk_matrix.reputation_risk.evidence}")
    print("=" * 60)


def test_case_1_high_growth_tech():
    """Case 1: High-growth tech. Sales strong, Risk skeptical, Moderator required."""
    loan = make_loan(
        "TechStart Inc",
        "Technology",
        5_000_000,
        CASE_1_FINANCIALS,
        compliance_flag=False,
    )
    run_case("Case 1: High-Growth Tech Startup", loan, CASE_1_AGENTS)
    assert abs(CASE_1_AGENTS["sales"].score - CASE_1_AGENTS["risk"].score) > 20
    assert loan.status in ("Approved", "Rejected")


def test_case_2_grey_list_compliance_veto():
    """Case 2: Grey list. Compliance veto, immediate rejection."""
    loan = make_loan(
        "ManufacturingCo Ltd",
        "Manufacturing",
        10_000_000,
        CASE_2_FINANCIALS,
        compliance_flag=True,  # flagged due to grey list
    )
    run_case("Case 2: Grey List Compliance Veto", loan, CASE_2_AGENTS)
    assert loan.status == "Rejected"
    assert loan.final_score == 0.0


def test_case_3_weak_profile_risk_rejection():
    """Case 3: Low revenue, high debt. Risk rejection."""
    loan = make_loan(
        "StrugglingBiz LLC",
        "Retail",
        1_500_000,
        CASE_3_FINANCIALS,
        compliance_flag=False,
    )
    run_case("Case 3: Weak Profile Risk Rejection", loan, CASE_3_AGENTS)
    assert loan.status == "Rejected"
    assert loan.final_score is not None and loan.final_score <= 20


def test_case_4_balanced_approved():
    """Case 4: Balanced firm. Approved without moderator."""
    loan = make_loan(
        "MidCap Industries",
        "Manufacturing",
        3_000_000,
        CASE_4_FINANCIALS,
        compliance_flag=False,
    )
    run_case("Case 4: Balanced Mid-Sized Firm", loan, CASE_4_AGENTS)
    assert loan.status == "Approved"
    assert loan.final_score is not None and loan.final_score > 20
