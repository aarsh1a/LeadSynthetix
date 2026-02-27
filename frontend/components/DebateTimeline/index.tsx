"use client";

import { useEffect, useState } from "react";
import type { AgentMemo } from "@/types";

interface DebateTimelineProps {
  memos: AgentMemo[];
}

const AGENT_COLORS: Record<string, string> = {
  Sales: "border-l-accent-teal bg-accent-teal/5",
  Risk: "border-l-amber-500/70 bg-amber-500/5",
  Compliance: "border-l-cyan-500/70 bg-cyan-500/5",
  Moderator: "border-l-violet-500/70 bg-violet-500/5",
};

/**
 * Group memos into rounds. The first 3 (S/R/C) or 4 (S/R/C/M) are Round 0.
 * After that, each set of 3-4 same-pattern agents is the next round.
 * Falls back to chronological order (by created_at / array index).
 */
function groupIntoRounds(memos: AgentMemo[]): { round: number; memo: AgentMemo }[] {
  if (memos.length === 0) return [];

  // Keep chronological order (already sorted by created_at from API)
  const result: { round: number; memo: AgentMemo }[] = [];
  const agentCounts: Record<string, number> = {};

  for (const memo of memos) {
    const count = agentCounts[memo.agent_type] || 0;
    result.push({ round: count, memo });
    agentCounts[memo.agent_type] = count + 1;
  }

  return result;
}

export default function DebateTimeline({ memos }: DebateTimelineProps) {
  const [visible, setVisible] = useState(0);
  const grouped = groupIntoRounds(memos);

  useEffect(() => {
    let idx = 0;
    const t = setInterval(() => {
      idx += 1;
      setVisible(idx);
      if (idx >= grouped.length) clearInterval(t);
    }, 400);
    return () => clearInterval(t);
  }, [grouped.length]);

  // Group by round for rendering
  const rounds: { round: number; items: { memo: AgentMemo }[] }[] = [];
  for (const g of grouped) {
    let roundGroup = rounds.find((r) => r.round === g.round);
    if (!roundGroup) {
      roundGroup = { round: g.round, items: [] };
      rounds.push(roundGroup);
    }
    roundGroup.items.push({ memo: g.memo });
  }

  let globalIdx = 0;

  return (
    <section className="animate-fade-in rounded-xl border border-surface-700 bg-surface-800/60 p-5">
      <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-slate-500">
        Debate Timeline
      </h2>
      <div className="space-y-5">
        {rounds.map((round) => (
          <div key={round.round}>
            <div className="mb-2 flex items-center gap-2">
              <div className="h-px flex-1 bg-surface-700" />
              <span className="text-[10px] font-medium uppercase tracking-widest text-slate-600">
                {round.round === 0 ? "Initial Review" : `Debate Round ${round.round}`}
              </span>
              <div className="h-px flex-1 bg-surface-700" />
            </div>
            <div className="space-y-3">
              {round.items.map((item) => {
                const i = globalIdx++;
                return (
                  <div
                    key={`${round.round}-${item.memo.agent_type}-${i}`}
                    className={`
                      overflow-hidden rounded-lg border-l-4 p-4
                      ${AGENT_COLORS[item.memo.agent_type] ?? "border-l-surface-500 bg-surface-700/30"}
                      ${i < visible ? "animate-stagger opacity-100" : "opacity-0 -translate-x-2"}
                    `}
                    style={{
                      animationDelay: i < visible ? `${i * 100}ms` : "0ms",
                      animationFillMode: "backwards",
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-medium text-slate-300">
                        {item.memo.agent_type}
                      </span>
                      <span className="font-mono text-xs text-slate-500">
                        Score {item.memo.risk_score ?? "—"}
                      </span>
                    </div>
                    <p className="mt-2 text-sm leading-relaxed text-slate-400">
                      {item.memo.content}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
