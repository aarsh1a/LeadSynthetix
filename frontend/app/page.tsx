import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-surface-900">
      <h1 className="font-mono text-2xl font-semibold tracking-tight text-slate-100">
        LendSynthetix
      </h1>
      <p className="mt-2 text-sm text-slate-500">
        Lending Decision Intelligence
      </p>
      <Link
        href="/dashboard"
        className="mt-8 rounded-lg bg-surface-700 px-6 py-3 text-sm font-medium text-slate-200 transition-colors hover:bg-surface-600 hover:text-accent-teal"
      >
        Go to Dashboard
      </Link>
    </main>
  );
}
