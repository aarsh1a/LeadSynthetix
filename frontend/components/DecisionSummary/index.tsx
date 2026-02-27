"use client";

import StatusBadge from "@/components/StatusBadge";
import type { LoanApplication, LoanStatus } from "@/types";

interface DecisionSummaryProps {
  loan: LoanApplication;
  pdfUrl: string;
}

export default function DecisionSummary({ loan, pdfUrl }: DecisionSummaryProps) {
  const status = (loan.status || "Pending") as LoanStatus;
  const score = loan.final_score != null ? loan.final_score.toFixed(1) : "—";
  const confidence =
    loan.confidence_score != null
      ? `${(loan.confidence_score * 100).toFixed(0)}%`
      : "—";
  const amount = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(loan.requested_amount);

  return (
    <aside className="space-y-6">
      <section className="animate-fade-in-scale rounded-xl border border-surface-700 bg-surface-800/60 p-5">
        <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-slate-500">
          Final Decision
        </h2>
        <div className="space-y-4">
          <div>
            <p className="text-xs text-slate-500">Status</p>
            <StatusBadge status={status} />
          </div>
          <div>
            <p className="text-xs text-slate-500">Final Score</p>
            <p className="font-mono text-2xl font-semibold text-slate-100">
              {score}
            </p>
            <p className="mt-1 text-xs text-slate-600">
              Approval Threshold: 20
            </p>
            {loan.final_score != null && (
              <p
                className={`mt-0.5 text-sm ${loan.final_score >= 20
                  ? "text-emerald-500/70"
                  : "text-red-400/70"
                  }`}
              >
                {Math.abs(loan.final_score - 20).toFixed(1)} points{" "}
                {loan.final_score >= 20 ? "above" : "below"} approval threshold
              </p>
            )}
          </div>
          <div>
            <p className="text-xs text-slate-500">Confidence</p>
            <div className="mt-1 flex items-center gap-2">
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-700">
                <div
                  className="h-full rounded-full bg-accent-teal transition-all duration-700"
                  style={{
                    width: `${(loan.confidence_score ?? 0) * 100}%`,
                  }}
                />
              </div>
              <span className="font-mono text-sm text-slate-300">
                {confidence}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-600">
              Derived from Sales–Risk variance
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Requested</p>
            <p className="font-mono text-slate-300">{amount}</p>
          </div>
        </div>
      </section>

      <a
        href={pdfUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="
          flex w-full items-center justify-center gap-2 rounded-xl border
          border-surface-600 bg-surface-800/60 px-4 py-3 text-sm font-medium
          text-slate-300 transition-all hover:border-accent-teal/50
          hover:bg-accent-teal/10 hover:text-accent-teal
        "
      >
        <svg
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        Export PDF
      </a>
    </aside>
  );
}
