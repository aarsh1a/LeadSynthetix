"use client";

import { useState, useRef, useEffect } from "react";

interface Message {
    role: "user" | "assistant";
    content: string;
}

interface ChatPanelProps {
    loanId: string;
    companyName: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Chat panel for asking questions about a loan decision.
 * Sends messages to POST /api/chat/ with loan context.
 */
export default function ChatPanel({ loanId, companyName }: ChatPanelProps) {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: "assistant",
            content: `Ask me anything about the ${companyName} loan decision — agent reasoning, risk factors, financials, or the final score.`,
        },
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [open, setOpen] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    }, [messages]);

    async function sendMessage() {
        const text = input.trim();
        if (!text || loading) return;

        const userMsg: Message = { role: "user", content: text };
        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            const res = await fetch(`${API_BASE}/api/chat/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    loan_id: loanId,
                    message: text,
                    history: messages.filter((m) => m.role !== "assistant" || messages.indexOf(m) > 0),
                }),
            });
            if (!res.ok) throw new Error("Chat request failed");
            const data = await res.json();
            setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
        } catch {
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "Sorry, I couldn't process that request. Please try again." },
            ]);
        } finally {
            setLoading(false);
        }
    }

    if (!open) {
        return (
            <button
                onClick={() => setOpen(true)}
                className="
          flex w-full items-center justify-center gap-2 rounded-xl border
          border-surface-600 bg-surface-800/60 px-4 py-3 text-sm font-medium
          text-slate-300 transition-all hover:border-violet-500/50
          hover:bg-violet-500/10 hover:text-violet-400
        "
            >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                    />
                </svg>
                Ask About This Decision
            </button>
        );
    }

    return (
        <section className="animate-fade-in rounded-xl border border-surface-700 bg-surface-800/60 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-surface-700 px-4 py-3">
                <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-violet-500 animate-pulse" />
                    <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500">
                        AI Chat
                    </h3>
                </div>
                <button
                    onClick={() => setOpen(false)}
                    className="text-slate-500 transition-colors hover:text-slate-300"
                >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            {/* Messages */}
            <div ref={scrollRef} className="h-64 overflow-y-auto px-4 py-3 space-y-3">
                {messages.map((msg, i) => (
                    <div
                        key={i}
                        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                        <div
                            className={`
                max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed
                ${msg.role === "user"
                                    ? "bg-accent-teal/20 text-slate-200"
                                    : "bg-surface-700/50 text-slate-400"
                                }
              `}
                        >
                            {msg.content}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-surface-700/50 rounded-lg px-3 py-2 text-sm text-slate-500">
                            <span className="inline-flex gap-1">
                                <span className="animate-bounce" style={{ animationDelay: "0ms" }}>·</span>
                                <span className="animate-bounce" style={{ animationDelay: "150ms" }}>·</span>
                                <span className="animate-bounce" style={{ animationDelay: "300ms" }}>·</span>
                            </span>
                        </div>
                    </div>
                )}
            </div>

            {/* Input */}
            <div className="border-t border-surface-700 px-4 py-3">
                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        sendMessage();
                    }}
                    className="flex gap-2"
                >
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask about the decision..."
                        disabled={loading}
                        className="
              flex-1 rounded-lg border border-surface-600 bg-surface-900 px-3 py-2
              text-sm text-slate-200 placeholder-slate-600
              focus:border-violet-500/50 focus:outline-none focus:ring-1 focus:ring-violet-500/30
              disabled:opacity-50
            "
                    />
                    <button
                        type="submit"
                        disabled={loading || !input.trim()}
                        className="
              rounded-lg bg-violet-600/80 px-3 py-2 text-sm font-medium text-white
              transition-all hover:bg-violet-600
              disabled:opacity-40 disabled:cursor-not-allowed
            "
                    >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                            />
                        </svg>
                    </button>
                </form>
                <p className="mt-1.5 text-center text-[10px] text-slate-600">
                    Powered by AI · Responses based on loan data &amp; agent memos
                </p>
            </div>
        </section>
    );
}
