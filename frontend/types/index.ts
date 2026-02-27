export type LoanStatus = "Pending" | "Approved" | "Rejected";

export interface LoanApplication {
  id: string;
  company_name: string;
  industry: string;
  requested_amount: number;
  extracted_financials?: ExtractionResult | null;
  status: LoanStatus;
  workflow_state: string;
  final_score?: number | null;
  compliance_flag: boolean;
  confidence_score?: number | null;
  created_at: string;
  agent_memos?: AgentMemo[];
}

export interface ExtractionResult {
  revenue?: number | null;
  debt?: number | null;
  dscr?: number | null;
  collateral_present?: boolean;
  compliance_keywords?: string[];
}

export interface AgentMemo {
  id: string;
  agent_type: "Sales" | "Risk" | "Compliance" | "Moderator";
  content: string;
  risk_score?: number | null;
  created_at: string;
}

export interface CategoryScore {
  score: number;
  evidence: string[];
}

export interface RiskMatrix {
  financial_risk: CategoryScore;
  growth_strength: CategoryScore;
  regulatory_risk: CategoryScore;
  reputation_risk: CategoryScore;
}
