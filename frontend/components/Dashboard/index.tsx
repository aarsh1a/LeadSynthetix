"use client";

import { useEffect, useState } from "react";
import UploadSection from "@/components/UploadSection";
import LoanCard from "@/components/LoanCard";
import { useAppStore } from "@/stores";
import { DEMO_CASES } from "@/lib/demo-cases";
import { confidenceFromVariance } from "@/lib/utils";
import type { LoanApplication } from "@/types";

// Mock loans for demo when no API list exists.
// Confidence is computed dynamically from representative Sales/Risk scores.
const MOCK_LOANS: LoanApplication[] = [
  {
    id: "demo-1",
    company_name: "Acme Corp",
    industry: "Manufacturing",
    requested_amount: 2_500_000,
    status: "Approved",
    workflow_state: "FINALIZED",
    final_score: 28.4,
    compliance_flag: false,
    confidence_score: confidenceFromVariance(80, 72), // sales 80, risk 72 → variance 8
    created_at: new Date().toISOString(),
  },
  {
    id: "demo-2",
    company_name: "Beta Industries",
    industry: "Technology",
    requested_amount: 1_200_000,
    status: "Pending",
    workflow_state: "INITIAL_REVIEW",
    final_score: null,
    compliance_flag: false,
    confidence_score: null, // not yet scored
    created_at: new Date().toISOString(),
  },
  {
    id: "demo-3",
    company_name: "Gamma Holdings",
    industry: "Finance",
    requested_amount: 5_000_000,
    status: "Rejected",
    workflow_state: "FINALIZED",
    final_score: 12.0,
    compliance_flag: true,
    confidence_score: 1.0, // compliance auto-reject → confidence 1.0
    created_at: new Date().toISOString(),
  },
];

export default function Dashboard() {
  const { loans, setLoans, addLoan } = useAppStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (loans.length === 0) {
      setLoans(MOCK_LOANS);
    }
  }, [loans.length, setLoans]);

  useEffect(() => {
    const onUpload = (e: CustomEvent) => {
      const data = e.detail;
      // Use real backend response data from the workflow
      const newLoan: LoanApplication = {
        id: data.loan_id || `upload-${Date.now()}`,
        company_name: data.company_name || "New Application",
        industry: "—",
        requested_amount: data.extracted_financials?.revenue || 0,
        status: data.status || "Pending",
        workflow_state: data.workflow_state || "FINALIZED",
        final_score: data.final_score ?? null,
        compliance_flag: data.compliance_flag ?? false,
        confidence_score: data.confidence_score ?? null,
        extracted_financials: data.extracted_financials ?? null,
        created_at: new Date().toISOString(),
        agent_memos: (data.agent_memos || []).map(
          (m: { agent_type: string; content: string; risk_score?: number }, i: number) => ({
            id: `memo-${Date.now()}-${i}`,
            agent_type: m.agent_type,
            content: m.content,
            risk_score: m.risk_score ?? null,
            created_at: new Date().toISOString(),
          }),
        ),
      };
      addLoan(newLoan);
    };
    window.addEventListener("upload-success", onUpload as EventListener);
    return () =>
      window.removeEventListener("upload-success", onUpload as EventListener);
  }, [addLoan]);

  const displayLoans = mounted && loans.length > 0 ? loans : MOCK_LOANS;

  return (
    <div className="min-h-screen">
      <header className="border-b border-surface-700 bg-surface-800/50 backdrop-blur-sm">
        <div className="mx-auto max-w-6xl px-4 py-4">
          <h1 className="font-mono text-lg font-semibold tracking-tight text-slate-100">
            LendSynthetix
          </h1>
          <p className="mt-0.5 text-xs text-slate-500">
            Lending Decision Intelligence
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        <section className="mb-10 animate-fade-in">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-medium uppercase tracking-wider text-slate-500">
              Upload
            </h2>
            <button
              onClick={() => {
                const demoLoans = DEMO_CASES.map((c) => c.loan);
                setLoans(demoLoans);
              }}
              className="
                rounded-lg border border-accent-teal/50 bg-accent-teal/10 px-4 py-2
                text-sm font-medium text-accent-teal transition-all
                hover:border-accent-teal hover:bg-accent-teal/20
              "
            >
              Simulate Cases
            </button>
          </div>
          <UploadSection />
        </section>

        <section>
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-slate-500">
            Loan Applications
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {displayLoans.map((loan, i) => (
              <LoanCard key={loan.id} loan={loan} index={i} />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
