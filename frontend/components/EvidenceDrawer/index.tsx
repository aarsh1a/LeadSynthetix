"use client";

import { useState } from "react";
import type { RiskMatrix } from "@/types";

interface EvidenceDrawerProps {
  riskMatrix: RiskMatrix;
}

const LABELS: Record<string, string> = {
  financial_risk: "Financial Risk",
  growth_strength: "Growth Strength",
  regulatory_risk: "Regulatory Risk",
  reputation_risk: "Reputation Risk",
};

export default function EvidenceDrawer({ riskMatrix }: EvidenceDrawerProps) {
  const [open, setOpen] = useState<string | null>(null);

  return (
    <section className="animate-fade-in rounded-xl border border-surface-700 bg-surface-800/60 p-5">
      <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-slate-500">
        Evidence Drawer
      </h2>
      <div className="space-y-2">
        {(Object.entries(riskMatrix) as [keyof RiskMatrix, { score: number; evidence: string[] }][]).map(
          ([key, cat]) => {
            const isOpen = open === key;
            return (
              <div
                key={key}
                className="overflow-hidden rounded-lg border border-surface-600"
              >
                <button
                  onClick={() => setOpen(isOpen ? null : key)}
                  className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-surface-700/50"
                >
                  <span className="text-sm font-medium text-slate-300">
                    {LABELS[key] ?? key}
                  </span>
                  <span className="font-mono text-xs text-slate-500">
                    {cat.evidence.length} items
                  </span>
                  <svg
                    className={`h-4 w-4 text-slate-500 transition-transform ${isOpen ? "rotate-180" : ""}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>
                <div
                  className={`grid transition-all duration-300 ${
                    isOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
                  }`}
                >
                  <div className="overflow-hidden">
                    <div className="border-t border-surface-600 bg-surface-900/50 px-4 py-3">
                      <ul className="space-y-1.5 text-xs text-slate-400">
                        {cat.evidence.map((e, i) => (
                          <li key={i} className="flex gap-2">
                            <span className="text-surface-500">•</span>
                            {e}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            );
          }
        )}
      </div>
    </section>
  );
}
