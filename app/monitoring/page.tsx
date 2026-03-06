"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { AgentSidebar, AgentConfig, defaultAgentConfig } from "@/components/AgentSidebar";

/* ─── Types ─── */
interface LeadEvent {
  type: string;
  payload: Record<string, any>;
  time: string;
}
interface LeadData {
  id: number;
  name: string;
  company: string;
  email: string;
  status: string;
  current_stage: string;
  events: LeadEvent[];
}
interface Metrics {
  sent: number;
  opened: number;
  replied: number;
  meetings: number;
  total: number;
  blocked: number;
}

/* ─── Navbar ─── */
function MonitoringNavbar() {
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

/* ─── Event Icon + Label Map ─── */
function eventIcon(type: string) {
  const map: Record<string, { icon: string; label: string; color: string }> = {
    email_sent: { icon: "📧", label: "Email sent", color: "#3b82f6" },
    email_opened: { icon: "👁", label: "Email opened", color: "#22c55e" },
    reply_received: { icon: "💬", label: "Reply received", color: "#a855f7" },
    positive_intent: { icon: "🎯", label: "Positive intent", color: "#f59e0b" },
    objection_detected: { icon: "🛡️", label: "Objection detected", color: "#ef4444" },
    meeting_booked: { icon: "📅", label: "Meeting booked", color: "#06b6d4" },
    clawbot_triggered: { icon: "🦅", label: "ClawBot alert", color: "#f59e0b" },
    followup_sent: { icon: "📬", label: "Follow-up sent", color: "#22c55e" },
    message_generated: { icon: "🤖", label: "AI drafted", color: "#8b5cf6" },
    blocklist_passed: { icon: "🛡️", label: "Cleared blocklist", color: "#6b7280" },
    blocked: { icon: "🚫", label: "Blocked", color: "#ef4444" },
    scheduled: { icon: "⏳", label: "Scheduled", color: "#6b7280" },
  };
  return map[type] || { icon: "▸", label: type, color: "#6b7280" };
}

/* ─── Lead Status Badge ─── */
function leadStatusBadge(events: LeadEvent[]) {
  const types = events.map(e => e.type);
  if (types.includes("meeting_booked")) return { label: "Meeting Booked", color: "#06b6d4", bg: "rgba(6,182,212,0.12)" };
  if (types.includes("positive_intent")) return { label: "Positive Intent", color: "#f59e0b", bg: "rgba(245,158,11,0.12)" };
  if (types.includes("objection_detected")) return { label: "Objection", color: "#ef4444", bg: "rgba(239,68,68,0.12)" };
  if (types.includes("reply_received")) return { label: "Replied", color: "#a855f7", bg: "rgba(168,85,247,0.12)" };
  if (types.includes("email_opened")) return { label: "Opened", color: "#22c55e", bg: "rgba(34,197,94,0.12)" };
  if (types.includes("email_sent")) return { label: "Sent", color: "#3b82f6", bg: "rgba(59,130,246,0.12)" };
  if (types.includes("blocked")) return { label: "Blocked", color: "#ef4444", bg: "rgba(239,68,68,0.12)" };
  return { label: "Pending", color: "#6b7280", bg: "rgba(107,114,128,0.12)" };
}

/* ─── Main Page ─── */
export default function MonitoringPage() {
  const [config, setConfig] = useState<AgentConfig>(defaultAgentConfig);
  const [metrics, setMetrics] = useState<Metrics>({ sent: 0, opened: 0, replied: 0, meetings: 0, total: 0, blocked: 0 });
  const [leads, setLeads] = useState<LeadData[]>([]);
  const [expandedLead, setExpandedLead] = useState<number | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [pulse, setPulse] = useState(false);

  const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchData = useCallback(() => {
    fetch(`${API}/api/campaigns/1/status`)
      .then(r => r.json())
      .then(data => {
        const m: Metrics = {
          sent: data.sent ?? 0,
          opened: data.opened ?? 0,
          replied: data.replied ?? 0,
          meetings: data.meetings_booked ?? 0,
          total: data.total_leads ?? 0,
          blocked: data.blocked ?? 0,
        };
        setMetrics(m);
        if (data.lead_progress) setLeads(data.lead_progress);
        setLastUpdated(new Date().toLocaleTimeString());
        setPulse(true);
        setTimeout(() => setPulse(false), 600);
      })
      .catch(() => { });
  }, [API]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("agentConfig");
      if (raw) setConfig(JSON.parse(raw) as AgentConfig);
    } catch { /* keep default */ }
    fetchData();
    // Auto-refresh every 10s
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // SSE for real-time updates
  useEffect(() => {
    const es = new EventSource(`${API}/api/campaigns/1/stream`);
    es.onmessage = () => {
      // Refresh data on any SSE event
      fetchData();
    };
    return () => es.close();
  }, [API, fetchData]);

  const metricCards = [
    { label: "Messages Sent", value: String(metrics.sent), sub: `${metrics.total} total leads`, color: "#3b82f6", icon: "📨", gradient: "from-blue-500/10 to-blue-600/5" },
    { label: "Email Opens", value: String(metrics.opened), sub: metrics.total > 0 ? `${((metrics.opened / metrics.total) * 100).toFixed(0)}% open rate` : "—", color: "#22c55e", icon: "👁", gradient: "from-emerald-500/10 to-emerald-600/5" },
    { label: "Reply Rate", value: metrics.total > 0 ? `${((metrics.replied / metrics.total) * 100).toFixed(1)}%` : "0%", sub: `${metrics.replied} replied`, color: "#a855f7", icon: "💬", gradient: "from-violet-500/10 to-violet-600/5" },
    { label: "Booked Calls", value: String(metrics.meetings), sub: "via ClawBot", color: "#f59e0b", icon: "📞", gradient: "from-amber-500/10 to-amber-600/5" },
  ];

  return (
    <div className="min-h-screen" style={{ background: "linear-gradient(135deg, #ffffff 0%, #dbeafe 40%, #3b82f6 100%)" }}>
      <MonitoringNavbar />
      {/* Ambient */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 right-1/4 w-96 h-96 rounded-full blur-[120px]" style={{ background: "rgba(59,130,246,0.15)" }} />
        <div className="absolute bottom-1/3 left-1/4 w-80 h-80 rounded-full blur-[100px]" style={{ background: "rgba(255,255,255,0.50)" }} />
      </div>

      {/* Header */}
      <div className="relative z-10 pl-72 pr-8 pt-24 pb-5 flex items-center justify-between" style={{ borderBottom: "1px solid rgba(59,130,246,0.15)" }}>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Monitoring</h1>
          <p className="text-sm mt-0.5 text-slate-500">
            Live performance &middot; Agent:{" "}
            <span className="text-blue-600 font-semibold">{config.agentName}</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-slate-400">{lastUpdated && `Updated ${lastUpdated}`}</span>
          <div
            className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl"
            style={{ background: "rgba(34,197,94,0.12)", border: "1px solid rgba(34,197,94,0.20)" }}
          >
            <div className="w-2 h-2 rounded-full bg-green-400 animate-live-dot" />
            <span className="text-xs font-semibold text-green-400">Live</span>
          </div>
        </div>
      </div>

      {/* Metric cards */}
      <div className="relative z-10 pl-72 pr-8 pt-6">
        <div className="grid grid-cols-4 gap-4">
          {metricCards.map(({ label, value, sub, color, icon, gradient }) => (
            <div
              key={label}
              className={`rounded-2xl p-4 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg cursor-default ${pulse ? "animate-fade-in-up" : ""}`}
              style={{
                background: "rgba(255,255,255,0.65)",
                backdropFilter: "blur(20px) saturate(1.8)",
                border: "1px solid rgba(255,255,255,0.90)",
                boxShadow: "0 4px 20px rgba(0,0,0,0.07)",
              }}
            >
              <div className="flex items-start justify-between mb-3">
                <p className="text-xs text-slate-500">{label}</p>
                <span className="text-base">{icon}</span>
              </div>
              <p className="text-2xl font-bold text-slate-900 transition-all duration-500">{value}</p>
              <p className="text-[11px] mt-1 font-semibold" style={{ color }}>{sub}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Lead Pipeline */}
      <div className="relative z-10 pl-72 pr-8 pt-6 pb-8">
        <div
          className="rounded-3xl p-6"
          style={{
            background: "rgba(255,255,255,0.55)",
            backdropFilter: "blur(24px) saturate(1.8)",
            border: "1px solid rgba(255,255,255,0.85)",
            boxShadow: "0 8px 40px rgba(0,0,0,0.08)",
          }}
        >
          <div className="flex items-center justify-between mb-6">
            <p className="text-[11px] font-bold tracking-widest uppercase text-slate-400">
              Lead Pipeline
            </p>
            <div className="flex items-center gap-2">
              {["Sent", "Opened", "Replied", "Meeting"].map((s, i) => (
                <span key={s} className="flex items-center gap-1 text-[10px] text-slate-400">
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: ["#3b82f6", "#22c55e", "#a855f7", "#06b6d4"][i] }} />
                  {s}
                </span>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            {leads.length === 0 && (
              <p className="text-sm text-slate-400 text-center py-8">Launch a campaign to see lead activity here...</p>
            )}
            {leads.map((lead) => {
              const badge = leadStatusBadge(lead.events || []);
              const isExpanded = expandedLead === lead.id;
              const replyEvent = (lead.events || []).find(e => e.type === "reply_received");
              const openCount = (lead.events || []).filter(e => e.type === "email_opened").length;
              const hasMeteting = (lead.events || []).some(e => e.type === "meeting_booked");

              return (
                <div key={lead.id} className="animate-fade-in-up">
                  {/* Lead Row */}
                  <div
                    onClick={() => setExpandedLead(isExpanded ? null : lead.id)}
                    className="flex items-center gap-4 py-3 px-4 rounded-xl transition-all duration-200 cursor-pointer hover:shadow-md"
                    style={{
                      background: isExpanded ? "rgba(255,255,255,0.95)" : "rgba(255,255,255,0.70)",
                      border: `1px solid ${isExpanded ? "rgba(59,130,246,0.25)" : "rgba(255,255,255,0.90)"}`,
                      boxShadow: isExpanded ? "0 4px 16px rgba(59,130,246,0.10)" : "0 2px 8px rgba(0,0,0,0.05)",
                    }}
                  >
                    {/* Status dot */}
                    <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: badge.color, boxShadow: `0 0 8px ${badge.color}50` }} />

                    {/* Name + Company */}
                    <div className="w-36 shrink-0">
                      <p className="text-sm font-semibold text-slate-800">{lead.name}</p>
                      <p className="text-[10px] text-slate-400">{lead.company}</p>
                    </div>

                    {/* Progress bar */}
                    <div className="flex-1 flex items-center gap-1.5">
                      {["email_sent", "email_opened", "reply_received", "meeting_booked"].map((stage, i) => {
                        const hasStage = (lead.events || []).some(e => e.type === stage);
                        const colors = ["#3b82f6", "#22c55e", "#a855f7", "#06b6d4"];
                        return (
                          <div key={stage} className="flex-1 h-1.5 rounded-full transition-all duration-500" style={{
                            background: hasStage ? colors[i] : "rgba(0,0,0,0.06)",
                            boxShadow: hasStage ? `0 0 6px ${colors[i]}40` : "none",
                          }} />
                        );
                      })}
                    </div>

                    {/* Badge */}
                    <span
                      className="text-[10px] font-semibold px-2.5 py-1 rounded-full shrink-0"
                      style={{ color: badge.color, background: badge.bg, border: `1px solid ${badge.color}25` }}
                    >
                      {badge.label}
                    </span>

                    {/* Expand arrow */}
                    <svg
                      className={`w-4 h-4 text-slate-400 shrink-0 transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`}
                      viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                    >
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </div>

                  {/* Expanded Detail */}
                  {isExpanded && (
                    <div
                      className="ml-6 mt-1 mb-2 rounded-xl p-4 animate-fade-in-up"
                      style={{
                        background: "rgba(248,250,252,0.90)",
                        border: "1px solid rgba(59,130,246,0.12)",
                      }}
                    >
                      {/* Quick Stats */}
                      <div className="flex items-center gap-4 mb-4">
                        <div className="flex items-center gap-1.5 text-[11px]">
                          <span>📧</span>
                          <span className="text-slate-500">{lead.email}</span>
                        </div>
                        {openCount > 0 && (
                          <div className="flex items-center gap-1.5 text-[11px]">
                            <span>👁</span>
                            <span className="text-emerald-600 font-semibold">{openCount} open{openCount > 1 ? "s" : ""}</span>
                          </div>
                        )}
                        {hasMeteting && (
                          <div className="flex items-center gap-1.5 text-[11px]">
                            <span>📅</span>
                            <span className="text-cyan-600 font-semibold">Meeting booked</span>
                          </div>
                        )}
                      </div>

                      {/* Reply Preview */}
                      {replyEvent && (
                        <div className="mb-4 p-3 rounded-lg" style={{ background: "rgba(168,85,247,0.06)", border: "1px solid rgba(168,85,247,0.15)" }}>
                          <p className="text-[10px] font-bold text-violet-500 uppercase tracking-wide mb-1">Reply</p>
                          <p className="text-sm text-slate-700 italic">&ldquo;{replyEvent.payload?.reply_text || replyEvent.payload?.body_preview || "No preview"}&rdquo;</p>
                          {replyEvent.payload?.intent && (
                            <span className={`inline-block mt-2 text-[10px] font-semibold px-2 py-0.5 rounded-full ${replyEvent.payload.intent === "positive"
                                ? "text-amber-700 bg-amber-50 border border-amber-200"
                                : "text-red-700 bg-red-50 border border-red-200"
                              }`}>
                              {replyEvent.payload.intent === "positive" ? "🎯 Positive Intent" : "🛡️ Objection"} • {Math.round((replyEvent.payload.confidence || 0) * 100)}%
                            </span>
                          )}
                        </div>
                      )}

                      {/* Event Timeline */}
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-2">Event Timeline</p>
                      <div className="space-y-1.5 max-h-48 overflow-y-auto">
                        {(lead.events || []).map((ev, i) => {
                          const info = eventIcon(ev.type);
                          const time = ev.time ? new Date(ev.time).toLocaleTimeString() : "";
                          return (
                            <div key={i} className="flex items-center gap-3 py-1.5 px-2 rounded-lg hover:bg-white/60 transition-colors">
                              <span className="text-sm">{info.icon}</span>
                              <span className="text-[11px] text-slate-600 flex-1">{info.label}</span>
                              {ev.payload?.subject && <span className="text-[10px] text-slate-400 truncate max-w-48">{ev.payload.subject}</span>}
                              <span className="text-[10px] text-slate-400 shrink-0">{time}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Draggable sidebar */}
      <AgentSidebar config={config} activePage="monitoring" />
    </div>
  );
}
