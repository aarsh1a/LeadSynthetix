"use client";

interface CompliancePanelProps {
  complianceKeywords: string[];
}

export default function CompliancePanel({ complianceKeywords }: CompliancePanelProps) {
  const hasIssues = complianceKeywords.length > 0;
  if (!hasIssues) return null;

  return (
    <div
      className="mb-6 animate-fade-in rounded-xl border border-amber-500/40 bg-amber-500/10 p-4"
      role="alert"
    >
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-amber-500/20">
          <svg
            className="h-4 w-4 text-amber-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <div>
          <h3 className="font-medium text-amber-200">Compliance Warning</h3>
          <p className="mt-1 text-sm text-amber-200/90">
            Keywords detected:{" "}
            <span className="font-mono">{complianceKeywords.join(", ")}</span>
          </p>
          <p className="mt-2 text-xs text-amber-200/70">
            Review required before approval.
          </p>
        </div>
      </div>
    </div>
  );
}
