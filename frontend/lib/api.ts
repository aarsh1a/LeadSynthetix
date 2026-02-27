const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function uploadPdf(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/ingest/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getLoan(id: string) {
  const res = await fetch(`${API_BASE}/api/loans/${id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getRiskMatrix(financials: Record<string, unknown>) {
  const res = await fetch(`${API_BASE}/api/scoring/risk-matrix`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(financials),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getLoans() {
  const res = await fetch(`${API_BASE}/api/loans/`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function chatAboutLoan(
  loanId: string,
  message: string,
  history: { role: string; content: string }[] = [],
) {
  const res = await fetch(`${API_BASE}/api/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ loan_id: loanId, message, history }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function getDecisionPdfUrl(loanId: string) {
  return `${API_BASE}/api/decision/${loanId}/memo/pdf`;
}
