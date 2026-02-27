"""
Run all 4 test scenarios and print outputs.
Execute: python -m tests.run_scenarios
Or: cd backend && PYTHONPATH=. python -m tests.run_scenarios
"""

import sys
from pathlib import Path

# Ensure backend/app is on path
backend = Path(__file__).resolve().parent.parent
if str(backend) not in sys.path:
    sys.path.insert(0, str(backend))

from tests.test_scenarios import (
    make_loan,
    run_case,
    CASE_1_FINANCIALS,
    CASE_1_AGENTS,
    CASE_2_FINANCIALS,
    CASE_2_AGENTS,
    CASE_3_FINANCIALS,
    CASE_3_AGENTS,
    CASE_4_FINANCIALS,
    CASE_4_AGENTS,
)


def main():
    print("\n" + "#" * 60)
    print("#  LendSynthetix — Automated Test Scenarios")
    print("#" * 60)

    # Case 1: High-growth tech
    loan1 = make_loan(
        "TechStart Inc",
        "Technology",
        5_000_000,
        CASE_1_FINANCIALS,
        compliance_flag=False,
    )
    run_case("Case 1: High-Growth Tech Startup", loan1, CASE_1_AGENTS)

    # Case 2: Grey list compliance veto
    loan2 = make_loan(
        "ManufacturingCo Ltd",
        "Manufacturing",
        10_000_000,
        CASE_2_FINANCIALS,
        compliance_flag=True,
    )
    run_case("Case 2: Grey List Compliance Veto", loan2, CASE_2_AGENTS)

    # Case 3: Weak profile risk rejection
    loan3 = make_loan(
        "StrugglingBiz LLC",
        "Retail",
        1_500_000,
        CASE_3_FINANCIALS,
        compliance_flag=False,
    )
    run_case("Case 3: Weak Profile Risk Rejection", loan3, CASE_3_AGENTS)

    # Case 4: Balanced approved
    loan4 = make_loan(
        "MidCap Industries",
        "Manufacturing",
        3_000_000,
        CASE_4_FINANCIALS,
        compliance_flag=False,
    )
    run_case("Case 4: Balanced Mid-Sized Firm", loan4, CASE_4_AGENTS)

    print("\n" + "#" * 60)
    print("#  All scenarios completed")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    main()
