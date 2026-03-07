"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { AgentSidebar, AgentConfig, defaultAgentConfig } from "@/components/AgentSidebar";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ─── Navbar ─── */
function AutopsyNavbar() {
    return (
        <nav className="fixed top-0 left-0 right-0 z-50 py-3 px-6">
            <div className="max-w-7xl mx-auto">
                <div
                    className="relative overflow-hidden rounded-2xl"
                    style={{
                        background: "rgba(255,255,255,0.65)",
                        backdropFilter: "blur(24px) saturate(2)",
                        border: "1px solid rgba(255,255,255,0.90)",
                        boxShadow: "0 4px 24px rgba(59,130,246,0.12)",
                    }}
                >
                    <div className="pointer-events-none absolute inset-x-0 top-0 h-px" style={{ background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.95), transparent)" }} />
                    <div className="pointer-events-none absolute inset-x-0 bottom-0 h-px opacity-40" style={{ background: "linear-gradient(90deg, transparent, rgba(59,130,246,0.6), transparent)" }} />
                    <div className="relative z-10 px-6 py-3 flex items-center justify-between">
                        <Link href="/" className="flex items-center gap-2.5">
                            <div className="relative flex items-center justify-center w-8 h-8">
                                <div className="absolute inset-0 rounded-lg bg-gradient-to-br from-blue-400 to-blue-600 opacity-90" />
                                <div className="absolute inset-px rounded-[7px] bg-white/20" />
                                <svg className="relative z-10 w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M12 2a4 4 0 0 1 4 4c0 1.95-1.4 3.58-3.25 3.93" />
                                    <path d="M8.56 13.44A4 4 0 1 0 12 18" />
                                    <path d="M12 18a4 4 0 0 0 4-4c0-1.1-.45-2.1-1.17-2.83" />
                                    <circle cx="12" cy="12" r="1.5" fill="currentColor" />
                                </svg>
                            </div>
                            <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-slate-900 via-slate-700 to-blue-600 bg-clip-text text-transparent">Synaptiq</span>
                        </Link>
                        <div className="hidden md:flex items-center gap-1">
                            {[{ href: "/", label: "Home" }, { href: "/#features", label: "Features" }, { href: "/#about", label: "About" }].map(({ href, label }) => (
                                <Link key={label} href={href} className="px-4 py-2 rounded-xl text-sm font-medium text-slate-600 hover:text-blue-600 hover:bg-white/60 transition-all duration-200">{label}</Link>
                            ))}
                        </div>
                        <Link href="/login" className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white transition-all duration-300 hover:scale-[1.03]" style={{ background: "linear-gradient(135deg, #3b82f6, #1d4ed8)", boxShadow: "0 0 16px rgba(59,130,246,0.30)" }}>
                            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>
                            Logout
                        </Link>
                    </div>
                </div>
            </div>
        </nav>
    );
}

/* ─── Metric config ─── */
const METRICS = [
    { key: "leads_processed", label: "Leads Processed", icon: "👥", color: "#3b82f6" },
    { key: "emails_sent", label: "Emails Sent", icon: "📧", color: "#22c55e" },
    { key: "blocked_competitor", label: "Competitor Blocked", icon: "🛡️", color: "#ef4444" },
    { key: "meetings_booked", label: "Meetings Booked", icon: "📅", color: "#06b6d4" },
    { key: "clawbot_interventions", label: "ClawBot Actions", icon: "🦅", color: "#f59e0b" },
    { key: "objections_handled", label: "Objections Handled", icon: "🧠", color: "#a855f7" },
    { key: "hindi_emails", label: "Hindi Emails (Sarvam)", icon: "🇮🇳", color: "#f97316" },
    { key: "human_hours_saved", label: "Human Hours Saved", icon: "⏰", color: "#10b981" },
];

/* ─── Main ─── */
export default function AutopsyPage() {
    const [config, setConfig] = useState<AgentConfig>(defaultAgentConfig);
    const [data, setData] = useState<Record<string, number> | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        try {
            const raw = localStorage.getItem("agentConfig");
            if (raw) setConfig(JSON.parse(raw) as AgentConfig);
        } catch { /* keep default */ }

        fetch(`${API}/api/campaigns/1/autopsy`)
            .then(r => r.json())
            .then(d => { setData(d); setLoading(false); })
            .catch(() => setLoading(false));
    }, []);

    return (
        <div className="min-h-screen" style={{ background: "linear-gradient(135deg, #ffffff 0%, #dbeafe 40%, #3b82f6 100%)" }}>
            <AutopsyNavbar />
            {/* Ambient */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div className="absolute top-0 left-1/3 w-96 h-96 rounded-full blur-[120px]" style={{ background: "rgba(59,130,246,0.15)" }} />
                <div className="absolute bottom-1/4 right-1/3 w-80 h-80 rounded-full blur-[100px]" style={{ background: "rgba(255,255,255,0.50)" }} />
            </div>

            {/* Header */}
            <div className="relative z-10 pl-72 pr-8 pt-24 pb-5 flex items-center justify-between" style={{ borderBottom: "1px solid rgba(59,130,246,0.15)" }}>
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">Campaign Autopsy</h1>
                    <p className="text-sm mt-0.5 text-slate-500">
                        End-of-campaign report &middot; Agent: <span className="text-blue-600 font-semibold">{config.agentName}</span>
                    </p>
                </div>
                <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl" style={{ background: "rgba(34,197,94,0.12)", border: "1px solid rgba(34,197,94,0.20)" }}>
                    <div className="w-2 h-2 rounded-full bg-green-400" />
                    <span className="text-xs font-semibold text-green-500">Complete</span>
                </div>
            </div>

            {/* Metrics Grid */}
            <div className="relative z-10 pl-72 pr-8 pt-6">
                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <div className="w-8 h-8 border-3 border-blue-400 border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    <>
                        <div className="grid grid-cols-4 gap-4">
                            {METRICS.map(({ key, label, icon, color }) => {
                                const value = data?.[key] ?? 0;
                                return (
                                    <div
                                        key={key}
                                        className="rounded-2xl p-5 transition-all duration-300 hover:scale-[1.03] hover:shadow-xl cursor-default group"
                                        style={{
                                            background: "rgba(255,255,255,0.65)",
                                            backdropFilter: "blur(20px) saturate(1.8)",
                                            border: "1px solid rgba(255,255,255,0.90)",
                                            boxShadow: "0 4px 20px rgba(0,0,0,0.07)",
                                        }}
                                    >
                                        <div className="flex items-start justify-between mb-3">
                                            <span className="text-2xl group-hover:scale-110 transition-transform duration-200">{icon}</span>
                                            <span
                                                className="text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full"
                                                style={{ color, background: `${color}15`, border: `1px solid ${color}25` }}
                                            >
                                                {key.replace(/_/g, " ").toUpperCase()}
                                            </span>
                                        </div>
                                        <p className="text-3xl font-bold text-slate-900 tabular-nums">
                                            {typeof value === "number" && !Number.isInteger(value) ? value.toFixed(1) : value}
                                        </p>
                                        <p className="text-xs text-slate-500 mt-1.5 font-medium">{label}</p>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Human Hours Saved Hero */}
                        <div
                            className="mt-6 rounded-2xl p-6 flex items-center gap-6"
                            style={{
                                background: "linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(59,130,246,0.08) 100%)",
                                border: "1px solid rgba(16,185,129,0.20)",
                                boxShadow: "0 4px 24px rgba(16,185,129,0.12)",
                            }}
                        >
                            <div className="w-16 h-16 rounded-2xl flex items-center justify-center shrink-0"
                                style={{ background: "rgba(16,185,129,0.12)", border: "1px solid rgba(16,185,129,0.25)" }}>
                                <span className="text-3xl">⏰</span>
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-slate-900">
                                    {data?.human_hours_saved ?? 0} human hours saved
                                </p>
                                <p className="text-sm text-slate-500 mt-1">
                                    {data?.emails_sent ?? 0} personalized emails × 0.06 hrs each = {data?.human_hours_saved ?? 0} hours of manual SDR work automated by Synaptiq
                                </p>
                            </div>
                        </div>

                        {/* Additional Stats Row */}
                        <div
                            className="mt-4 rounded-2xl p-5 grid grid-cols-3 gap-6"
                            style={{
                                background: "rgba(255,255,255,0.55)",
                                backdropFilter: "blur(20px) saturate(1.8)",
                                border: "1px solid rgba(255,255,255,0.85)",
                                boxShadow: "0 4px 20px rgba(0,0,0,0.06)",
                            }}
                        >
                            <div className="text-center">
                                <p className="text-xs text-slate-400 uppercase tracking-widest font-bold mb-1">Spam Risk</p>
                                <p className="text-lg font-bold text-emerald-600">{data?.spam_score ?? "2.1"} <span className="text-xs font-semibold text-emerald-500">LOW</span></p>
                            </div>
                            <div className="text-center">
                                <p className="text-xs text-slate-400 uppercase tracking-widest font-bold mb-1">Avg Fields / Email</p>
                                <p className="text-lg font-bold text-blue-600">{data?.avg_fields_per_email ?? "3.4"}</p>
                            </div>
                            <div className="text-center">
                                <p className="text-xs text-slate-400 uppercase tracking-widest font-bold mb-1">DNC Blocked</p>
                                <p className="text-lg font-bold text-red-500">{data?.blocked_dnc ?? 0}</p>
                            </div>
                        </div>

                        {/* Back to dashboard */}
                        <div className="mt-6 pb-8 flex justify-center">
                            <Link
                                href="/dashboard"
                                className="px-6 py-2.5 rounded-xl text-sm font-semibold text-white transition-all duration-300 hover:scale-[1.03] hover:brightness-110"
                                style={{ background: "linear-gradient(135deg, #3b82f6, #1d4ed8)", boxShadow: "0 0 16px rgba(59,130,246,0.30)" }}
                            >
                                ← Back to Workflow
                            </Link>
                        </div>
                    </>
                )}
            </div>

            <AgentSidebar config={config} activePage="monitoring" />
        </div>
    );
}
