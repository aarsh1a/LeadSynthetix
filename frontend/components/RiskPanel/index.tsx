"use client";

import { useMemo } from "react";
import type { RiskMatrix } from "@/types";

interface RiskPanelProps {
  riskMatrix: RiskMatrix;
}

function RiskGauge({ value, label }: { value: number; label: string }) {
  const pct = Math.min(100, (value / 10) * 100);
  const dashOffset = 283 - (283 * pct) / 100;
  const color =
    value <= 3
      ? "stroke-accent-teal"
      : value <= 6
        ? "stroke-amber-500"
        : "stroke-accent-rose";

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 100 100" className="h-20 w-20 -rotate-90">
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          className="text-surface-600"
        />
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray="283"
          strokeDashoffset={dashOffset}
          className={`${color} transition-all duration-700`}
        />
      </svg>
      <span className="mt-1 font-mono text-lg font-medium text-slate-200">
        {value}/10
      </span>
      <span className="text-xs text-slate-500">{label}</span>
    </div>
  );
}

function aggregateRisk(rm: RiskMatrix): number {
  const r =
    (rm.financial_risk.score + rm.regulatory_risk.score + rm.reputation_risk.score) / 3;
  const g = rm.growth_strength.score;
  return Math.round((r * 0.6 - g * 0.1 + 5) / 1.5); // normalized 1-10
}

export default function RiskPanel({ riskMatrix }: RiskPanelProps) {
  const overallRisk = useMemo(
    () => Math.min(10, Math.max(1, aggregateRisk(riskMatrix))),
    [riskMatrix]
  );

  const rows = [
    { label: "Financial Risk", cat: riskMatrix.financial_risk, invert: false },
    { label: "Growth Strength", cat: riskMatrix.growth_strength, invert: true },
    { label: "Regulatory Risk", cat: riskMatrix.regulatory_risk, invert: false },
    { label: "Reputation Risk", cat: riskMatrix.reputation_risk, invert: false },
  ];

  return (
    <section className="animate-fade-in rounded-xl border border-surface-700 bg-surface-800/60 p-5">
      <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-slate-500">
        Risk Matrix
      </h2>

      <div className="mb-6 flex justify-around border-b border-surface-600 pb-6">
        <RiskGauge value={overallRisk} label="Overall Risk" />
        <RiskGauge value={riskMatrix.financial_risk.score} label="Financial" />
        <RiskGauge value={riskMatrix.regulatory_risk.score} label="Regulatory" />
      </div>

      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-surface-600">
            <th className="pb-3 font-medium text-slate-400">Category</th>
            <th className="pb-3 font-mono font-medium text-slate-400">Score</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ label, cat }, i) => (
            <tr
              key={label}
              className="border-b border-surface-700/80 transition-colors hover:bg-surface-700/30"
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <td className="py-3 text-slate-300">{label}</td>
              <td className="py-3 font-mono text-slate-200">{cat.score}/10</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
