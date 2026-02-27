"use client";

import Link from "next/link";
import StatusBadge from "./StatusBadge";
import type { LoanApplication, LoanStatus } from "@/types";

interface LoanCardProps {
  loan: LoanApplication;
  index?: number;
}

export default function LoanCard({ loan, index = 0 }: LoanCardProps) {
  const status = (loan.status || "Pending") as LoanStatus;
  const score =
    loan.final_score != null
      ? loan.final_score.toFixed(1)
      : "—";
  const amount = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(loan.requested_amount);

  return (
    <Link
      href={`/decision/${loan.id}`}
      className="
        group block rounded-xl border border-surface-600 bg-surface-800/60
        p-4 transition-all duration-300 hover:border-surface-500 hover:bg-surface-800
        hover:shadow-glow/30 animate-fade-in
      "
      style={{ animationDelay: `${index * 60}ms`, animationFillMode: "backwards" }}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium text-slate-100 group-hover:text-accent-teal transition-colors">
            {loan.company_name}
          </p>
          <p className="mt-0.5 text-xs text-slate-500">{loan.industry}</p>
          <p className="mt-2 font-mono text-sm text-slate-400">{amount}</p>
        </div>
        <StatusBadge status={status} size="sm" />
      </div>
      <div className="mt-3 flex items-center justify-between border-t border-surface-600/80 pt-3">
        <span className="text-xs text-slate-500">Score</span>
        <span className="font-mono text-sm text-slate-300">{score}</span>
      </div>
    </Link>
  );
}
