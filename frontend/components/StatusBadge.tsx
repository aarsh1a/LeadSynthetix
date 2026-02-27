"use client";

import type { LoanStatus } from "@/types";

interface StatusBadgeProps {
  status: LoanStatus;
  size?: "sm" | "md";
}

const styles: Record<LoanStatus, string> = {
  Pending:
    "bg-amber-500/15 text-amber-400 border-amber-500/30 shadow-glow-amber/30",
  Approved:
    "bg-emerald-500/15 text-accent-teal border-emerald-500/30 shadow-glow",
  Rejected:
    "bg-rose-500/15 text-accent-rose border-rose-500/30 shadow-glow-rose/30",
};

export default function StatusBadge({ status, size = "md" }: StatusBadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center rounded-full border px-2.5 font-mono text-xs font-medium
        ${styles[status]}
        ${size === "sm" ? "py-0.5" : "py-1"}
      `}
    >
      <span
        className={`mr-1.5 h-1.5 w-1.5 rounded-full ${
          status === "Approved"
            ? "bg-accent-teal"
            : status === "Rejected"
              ? "bg-accent-rose"
              : "bg-amber-400 animate-pulse"
        }`}
      />
      {status}
    </span>
  );
}
