"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState, useMemo } from "react";
import DebateTimeline from "@/components/DebateTimeline";
import RiskPanel from "@/components/RiskPanel";
import CompliancePanel from "@/components/CompliancePanel";
import EvidenceDrawer from "@/components/EvidenceDrawer";
import DecisionSummary from "@/components/DecisionSummary";
import ChatPanel from "@/components/ChatPanel";
import type { LoanApplication, AgentMemo, RiskMatrix } from "@/types";
import { useAppStore } from "@/stores";
import { getLoan, getRiskMatrix, getDecisionPdfUrl } from "@/lib/api";
import { getDemoCase } from "@/lib/demo-cases";

const FALLBACK_LOAN: LoanApplication = {
  id: "demo-1",
  company_name: "Acme Corp",
  industry: "Manufacturing",
  requested_amount: 2_500_000,
  status: "Approved",
  workflow_state: "FINALIZED",
  final_score: 28.4,
  compliance_flag: false,
  confidence_score: 0.82,
  extracted_financials: {
    revenue: 12_000_000,
    debt: 5_000_000,
    dscr: 1.25,
    collateral_present: true,
    compliance_keywords: [],
  },
  created_at: new Date().toISOString(),
};

const FALLBACK_MEMOS: AgentMemo[] = [
  {
    id: "1",
    agent_type: "Sales",
    content: "Strong revenue growth and collateral support. Recommend approval.",
    risk_score: 72,
    created_at: new Date().toISOString(),
  },
  {
    id: "2",
    agent_type: "Risk",
    content: "DSCR adequate. Leverage moderate. Proceed with covenant monitoring.",
    risk_score: 58,
    created_at: new Date().toISOString(),
  },
  {
    id: "3",
    agent_type: "Compliance",
    content: "No compliance issues identified. Clean screening.",
    risk_score: 88,
    created_at: new Date().toISOString(),
  },
  {
    id: "4",
    agent_type: "Moderator",
    content: "Consensus reached. Risk-adjusted score supports approval.",
    risk_score: 68,
    created_at: new Date().toISOString(),
  },
];

const FALLBACK_RISK: RiskMatrix = {
  financial_risk: { score: 4, evidence: ["DSCR 1.25 adequate buffer", "Debt/Revenue 0.4x"] },
  growth_strength: { score: 8, evidence: ["Revenue $12M solid base", "Collateral supports capacity"] },
  regulatory_risk: { score: 1, evidence: ["No compliance keywords"] },
  reputation_risk: { score: 1, evidence: ["No reputation keywords"] },
};

export default function DecisionPage() {
  const params = useParams();
  const id = params.id as string;
  const { loans } = useAppStore();
  const [loan, setLoan] = useState<LoanApplication | null>(null);
  const [apiMemos, setApiMemos] = useState<AgentMemo[] | null>(null);
  const [apiRisk, setApiRisk] = useState<RiskMatrix | null>(null);

  const demoCase = useMemo(() => getDemoCase(id), [id]);

  // Fetch real loan data from API for non-demo loans
  useEffect(() => {
    if (demoCase) {
      setLoan(demoCase.loan);
      return;
    }

    // First check local store (from recent upload)
    const storeLoan = loans.find((l) => l.id === id);
    if (storeLoan) {
      setLoan(storeLoan);
      if (storeLoan.agent_memos && storeLoan.agent_memos.length > 0) {
        setApiMemos(storeLoan.agent_memos);
      }
    }

    // Also fetch from API for latest data (will overwrite store data)
    getLoan(id)
      .then((data) => {
        const loanData: LoanApplication = {
          id: data.id,
          company_name: data.company_name,
          industry: data.industry,
          requested_amount: data.requested_amount,
          extracted_financials: data.extracted_financials,
          status: data.status,
          workflow_state: data.workflow_state,
          final_score: data.final_score,
          compliance_flag: data.compliance_flag,
          confidence_score: data.confidence_score,
          created_at: data.created_at,
        };
        setLoan(loanData);
        if (data.agent_memos && data.agent_memos.length > 0) {
          setApiMemos(data.agent_memos);
        }
        // Fetch risk matrix if we have financials
        if (data.extracted_financials) {
          getRiskMatrix(data.extracted_financials)
            .then(setApiRisk)
            .catch(() => { });
        }
      })
      .catch(() => {
        // API unavailable — fall back to store or fallback
        if (!storeLoan) setLoan(FALLBACK_LOAN);
      });
  }, [id, loans, demoCase]);

  const data = demoCase?.loan ?? loan ?? FALLBACK_LOAN;
  const memos = demoCase?.memos ?? apiMemos ?? FALLBACK_MEMOS;
  const riskMatrix = demoCase?.riskMatrix ?? apiRisk ?? FALLBACK_RISK;
  const financials = data.extracted_financials || {};

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-surface-700 bg-surface-900/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <Link
            href="/dashboard"
            className="text-sm text-slate-500 transition-colors hover:text-accent-teal"
          >
            ← Dashboard
          </Link>
          <h1 className="font-mono text-lg font-semibold text-slate-100">
            {data.company_name}
          </h1>
          <span className="text-xs text-slate-500">{data.id}</span>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        {(financials.compliance_keywords?.length ?? 0) > 0 && (
          <CompliancePanel complianceKeywords={financials.compliance_keywords ?? []} />
        )}

        <div className="grid gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-8">
            <DebateTimeline memos={memos} />
            <RiskPanel riskMatrix={riskMatrix} />
            <EvidenceDrawer riskMatrix={riskMatrix} />
          </div>

          <div className="space-y-6">
            <DecisionSummary loan={data} pdfUrl={getDecisionPdfUrl(id)} />
            <ChatPanel loanId={id} companyName={data.company_name} />
          </div>
        </div>
      </main>
    </div>
  );
}
