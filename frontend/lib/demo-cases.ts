import type { LoanApplication, AgentMemo, RiskMatrix } from "@/types";
import { confidenceFromVariance } from "@/lib/utils";

export interface DemoCase {
  loan: LoanApplication;
  memos: AgentMemo[];
  riskMatrix: RiskMatrix;
}

const now = () => new Date().toISOString();

/**
 * Derive confidence_score for a demo case from its Sales and Risk memos.
 * For compliance-flag auto-rejects confidence is always 1.0.
 */
function applyConfidence(c: DemoCase): DemoCase {
  if (c.loan.compliance_flag) {
    c.loan.confidence_score = 1.0;
    return c;
  }
  const salesMemo = c.memos.find((m) => m.agent_type === "Sales");
  const riskMemo = c.memos.find((m) => m.agent_type === "Risk");
  if (salesMemo?.risk_score != null && riskMemo?.risk_score != null) {
    c.loan.confidence_score = confidenceFromVariance(
      salesMemo.risk_score,
      riskMemo.risk_score,
    );
  }
  return c;
}

// Confidence is computed dynamically via applyConfidence — no hardcoded values.
export const DEMO_CASES: DemoCase[] = [
  {
    loan: {
      id: "case-1",
      company_name: "TechStart Inc",
      industry: "Technology",
      requested_amount: 5_000_000,
      status: "Rejected",
      workflow_state: "FINALIZED",
      final_score: 16.0,
      compliance_flag: false,
      extracted_financials: {
        revenue: 25_000_000,
        debt: 8_000_000,
        dscr: 1.1,
        collateral_present: false,
        compliance_keywords: [],
      },
      created_at: now(),
    },
    memos: [
      {
        id: "c1-1",
        agent_type: "Sales",
        content: "Strong growth trajectory. Revenue $25M with expansion potential. Recommend approval.",
        risk_score: 85,
        created_at: now(),
      },
      {
        id: "c1-2",
        agent_type: "Risk",
        content: "DSCR weak at 1.1, no collateral. High risk profile. Skeptical.",
        risk_score: 45,
        created_at: now(),
      },
      {
        id: "c1-3",
        agent_type: "Compliance",
        content: "No compliance issues identified.",
        risk_score: 90,
        created_at: now(),
      },
      {
        id: "c1-4",
        agent_type: "Moderator",
        content: "Moderator synthesis: Sales/Risk divergence > 20. Blended view suggests caution despite growth.",
        risk_score: 62,
        created_at: now(),
      },
    ],
    riskMatrix: {
      financial_risk: {
        score: 6,
        evidence: ["DSCR 1.10 below 1.25 typical covenant", "Debt/Revenue 0.3x"],
      },
      growth_strength: {
        score: 7,
        evidence: ["Revenue $25.0M solid base", "DSCR 1.10 constrains growth capacity"],
      },
      regulatory_risk: { score: 1, evidence: ["No compliance keywords detected"] },
      reputation_risk: { score: 1, evidence: ["No reputation risk keywords detected"] },
    },
  },
  {
    loan: {
      id: "case-2",
      company_name: "ManufacturingCo Ltd",
      industry: "Manufacturing",
      requested_amount: 10_000_000,
      status: "Rejected",
      workflow_state: "FINALIZED",
      final_score: 0.0,
      compliance_flag: true,
      extracted_financials: {
        revenue: 50_000_000,
        debt: 12_000_000,
        dscr: 1.4,
        collateral_present: true,
        compliance_keywords: ["grey list"],
      },
      created_at: now(),
    },
    memos: [
      {
        id: "c2-1",
        agent_type: "Sales",
        content: "Strong assets and revenue base. Solid manufacturing profile.",
        risk_score: 75,
        created_at: now(),
      },
      {
        id: "c2-2",
        agent_type: "Risk",
        content: "Solid financial profile. DSCR adequate, collateral present.",
        risk_score: 70,
        created_at: now(),
      },
      {
        id: "c2-3",
        agent_type: "Compliance",
        content: "Director on grey list. Immediate block. Compliance veto.",
        risk_score: 15,
        created_at: now(),
      },
    ],
    riskMatrix: {
      financial_risk: {
        score: 4,
        evidence: ["DSCR 1.40 adequate buffer", "Debt/Revenue 0.2x", "Collateral present reduces financial risk"],
      },
      growth_strength: {
        score: 9,
        evidence: ["Revenue $50M indicates scale", "DSCR 1.40 suggests strong cash flow", "Collateral supports financing capacity"],
      },
      regulatory_risk: { score: 3, evidence: ["Keyword detected: grey list"] },
      reputation_risk: { score: 3, evidence: ["Keyword detected: grey list"] },
    },
  },
  {
    loan: {
      id: "case-3",
      company_name: "StrugglingBiz LLC",
      industry: "Retail",
      requested_amount: 1_500_000,
      status: "Rejected",
      workflow_state: "FINALIZED",
      final_score: 12.0,
      compliance_flag: false,
      extracted_financials: {
        revenue: 2_000_000,
        debt: 4_000_000,
        dscr: 0.8,
        collateral_present: false,
        compliance_keywords: [],
      },
      created_at: now(),
    },
    memos: [
      {
        id: "c3-1",
        agent_type: "Sales",
        content: "Growth potential in niche market. Some upside.",
        risk_score: 55,
        created_at: now(),
      },
      {
        id: "c3-2",
        agent_type: "Risk",
        content: "Weak DSCR 0.8, high leverage (2x Debt/Revenue). Reject.",
        risk_score: 25,
        created_at: now(),
      },
      {
        id: "c3-3",
        agent_type: "Compliance",
        content: "Clean. No compliance flags.",
        risk_score: 85,
        created_at: now(),
      },
    ],
    riskMatrix: {
      financial_risk: {
        score: 9,
        evidence: [
          "DSCR 0.80 below 1.0 (cannot cover debt service)",
          "Debt/Revenue 2.0x moderate leverage",
        ],
      },
      growth_strength: {
        score: 4,
        evidence: ["Revenue $2.0M", "DSCR 0.80 constrains growth capacity"],
      },
      regulatory_risk: { score: 1, evidence: ["No compliance keywords detected"] },
      reputation_risk: { score: 1, evidence: ["No reputation risk keywords detected"] },
    },
  },
  {
    loan: {
      id: "case-4",
      company_name: "MidCap Industries",
      industry: "Manufacturing",
      requested_amount: 3_000_000,
      status: "Approved",
      workflow_state: "FINALIZED",
      final_score: 20.4,
      compliance_flag: false,
      extracted_financials: {
        revenue: 15_000_000,
        debt: 5_000_000,
        dscr: 1.35,
        collateral_present: true,
        compliance_keywords: [],
      },
      created_at: now(),
    },
    memos: [
      {
        id: "c4-1",
        agent_type: "Sales",
        content: "Healthy profile. Strong DSCR, collateral. Approve.",
        risk_score: 86,
        created_at: now(),
      },
      {
        id: "c4-2",
        agent_type: "Risk",
        content: "Strong DSCR 1.35, manageable leverage. Proceed.",
        risk_score: 35,
        created_at: now(),
      },
      {
        id: "c4-3",
        agent_type: "Compliance",
        content: "No flags. Clean.",
        risk_score: 88,
        created_at: now(),
      },
    ],
    riskMatrix: {
      financial_risk: {
        score: 4,
        evidence: ["DSCR 1.35 adequate buffer", "Debt/Revenue 0.3x", "Collateral present reduces financial risk"],
      },
      growth_strength: {
        score: 8,
        evidence: ["Revenue $15.0M solid base", "DSCR 1.35 supports growth capacity", "Collateral supports financing capacity"],
      },
      regulatory_risk: { score: 1, evidence: ["No compliance keywords detected"] },
      reputation_risk: { score: 1, evidence: ["No reputation risk keywords detected"] },
    },
  },
].map(applyConfidence);

const DEMO_CASE_IDS = new Set(DEMO_CASES.map((c) => c.loan.id));

export function isDemoCase(id: string): boolean {
  return DEMO_CASE_IDS.has(id);
}

export function getDemoCase(id: string): DemoCase | null {
  return DEMO_CASES.find((c) => c.loan.id === id) ?? null;
}
