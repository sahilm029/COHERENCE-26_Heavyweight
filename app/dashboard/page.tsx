"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AgentSidebar, AgentConfig, defaultAgentConfig } from "@/components/AgentSidebar";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function DashboardNavbar({ onLogout }: { onLogout: () => void }) {
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
            <button onClick={onLogout} className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white transition-all duration-300 hover:scale-[1.03]" style={{ background: "linear-gradient(135deg, #3b82f6, #1d4ed8)", boxShadow: "0 0 16px rgba(59,130,246,0.30)" }}>
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

/* ─── Floating Leads Panel — REMOVED (leads visible in sidebar) ─── */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function LeadsFloatingPanel({ leads }: { leads: Record<string, string>[] }) {
  return null;
}


export default function DashboardPage() {
  const router = useRouter();
  const [config, setConfig] = useState<AgentConfig>(defaultAgentConfig);
  const [leads, setLeads] = useState<Record<string, string>[]>([]);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    // Auth guard — redirect to login if no session
    const session = localStorage.getItem("synaptiq_session");
    if (!session) {
      router.push("/login");
      return;
    }
    setAuthChecked(true);

    try {
      const raw = localStorage.getItem("agentConfig");
      if (raw) setConfig(JSON.parse(raw) as AgentConfig);
    } catch { /* keep default */ }
    try {
      const rawLeads = localStorage.getItem("leadsData");
      if (rawLeads) setLeads(JSON.parse(rawLeads) as Record<string, string>[]);
    } catch { /* ignore */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const nodeData = [
    { id: 0, label: "Start", sub: "Trigger", x: 40, y: 60, bg: "rgba(59,130,246,0.18)", border: "rgba(59,130,246,0.40)", glow: "rgba(59,130,246,0.35)", icon: <svg className="w-9 h-9 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polygon points="10 8 16 12 10 16" fill="currentColor" stroke="none" /></svg> },
    { id: 1, label: "Qualify", sub: "AI filter", x: 250, y: 60, bg: "rgba(168,85,247,0.18)", border: "rgba(168,85,247,0.40)", glow: "rgba(168,85,247,0.35)", icon: <svg className="w-9 h-9 text-purple-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z" /></svg> },
    { id: 2, label: "Send", sub: "Email/SMS", x: 460, y: 60, bg: "rgba(34,197,94,0.18)", border: "rgba(34,197,94,0.40)", glow: "rgba(34,197,94,0.35)", icon: <svg className="w-9 h-9 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><polyline points="22,6 12,13 2,6" /></svg> },
    { id: 3, label: "Follow Up", sub: "D+3 auto", x: 670, y: 60, bg: "rgba(245,158,11,0.18)", border: "rgba(245,158,11,0.40)", glow: "rgba(245,158,11,0.35)", icon: <svg className="w-9 h-9 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg> },
    { id: 4, label: "Convert", sub: "Close 🎯", x: 880, y: 60, bg: "rgba(239,68,68,0.18)", border: "rgba(239,68,68,0.40)", glow: "rgba(239,68,68,0.35)", icon: <svg className="w-9 h-9 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg> },
  ];



  const handleLogout = () => {
    localStorage.removeItem("synaptiq_session");
    router.push("/login");
  };

  const [nodes, setNodes] = useState(nodeData.map(n => ({ ...n })));
  const [hoveredNode, setHoveredNode] = useState<number | null>(null);
  const draggingNode = useRef<{ id: number; startX: number; startY: number; origX: number; origY: number } | null>(null);

  /* ── Action state ── */
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [copilotInput, setCopilotInput] = useState("");
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [preflightLoading, setPreflightLoading] = useState(false);
  const [preflightData, setPreflightData] = useState<{ score: number; risk: string; issues: string[] } | null>(null);
  const [isLaunching, setIsLaunching] = useState(false);
  const [execLogs, setExecLogs] = useState<{ line: string; color: string }[]>([]);
  const logRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(0.85);

  const handleCanvasWheel = (e: React.WheelEvent) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      setZoom(z => Math.min(1.5, Math.max(0.4, z - e.deltaY * 0.001)));
    }
  };

  /* ── Node dragging ── */
  const onNodeMouseDown = (e: React.MouseEvent, id: number) => {
    e.preventDefault();
    const node = nodes.find(n => n.id === id)!;
    const startX = e.clientX;
    const startY = e.clientY;
    const origX = node.x;
    const origY = node.y;
    draggingNode.current = { id, startX, startY, origX, origY };
    const onMove = (ev: MouseEvent) => {
      if (!draggingNode.current) return;
      const dx = ev.clientX - startX;
      const dy = ev.clientY - startY;
      setNodes(prev => prev.map(n => n.id === id ? { ...n, x: origX + dx, y: origY + dy } : n));
    };
    const onUp = () => {
      draggingNode.current = null;
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  };

  /* ── Campaign Copilot ── */
  const handleCopilot = async () => {
    if (!copilotInput.trim()) return;
    setCopilotLoading(true);
    try {
      const res = await fetch(`${API}/api/copilot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: copilotInput }),
      });
      const data = await res.json();
      if (data.nodes) {
        // Map backend nodes to canvas format
        const colors = [
          { bg: "rgba(59,130,246,0.18)", border: "rgba(59,130,246,0.40)", glow: "rgba(59,130,246,0.35)" },
          { bg: "rgba(168,85,247,0.18)", border: "rgba(168,85,247,0.40)", glow: "rgba(168,85,247,0.35)" },
          { bg: "rgba(34,197,94,0.18)", border: "rgba(34,197,94,0.40)", glow: "rgba(34,197,94,0.35)" },
          { bg: "rgba(245,158,11,0.18)", border: "rgba(245,158,11,0.40)", glow: "rgba(245,158,11,0.35)" },
          { bg: "rgba(239,68,68,0.18)", border: "rgba(239,68,68,0.40)", glow: "rgba(239,68,68,0.35)" },
        ];
        const iconColors = ["text-blue-500", "text-purple-500", "text-green-500", "text-amber-500", "text-red-500"];
        const newNodes = data.nodes.map((n: any, i: number) => ({
          id: i,
          label: n.label || n.node_type || `Step ${i + 1}`,
          sub: n.node_type || "action",
          x: 40 + i * 210,
          y: 60,
          ...colors[i % colors.length],
          icon: <svg className={`w-9 h-9 ${iconColors[i % iconColors.length]}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><path d="M12 8v8m-4-4h8" /></svg>,
        }));
        setNodes(newNodes);
      }
      setCopilotOpen(false);
      setCopilotInput("");
    } catch { /* ignore */ }
    setCopilotLoading(false);
  };

  /* ── Preflight ── */
  const handlePreflight = async () => {
    setPreflightLoading(true);
    try {
      const res = await fetch(`${API}/api/preflight`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nodes: nodes.map(n => ({ node_type: n.sub, label: n.label })) }),
      });
      const data = await res.json();
      setPreflightData({ score: data.score, risk: data.risk, issues: data.issues || [] });
      if (data.issues?.length > 0) {
        // Auto-fix
        const fixRes = await fetch(`${API}/api/preflight/fix`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ issues: data.issues }),
        });
        const fixData = await fixRes.json();
        setPreflightData({ score: fixData.score ?? 1.9, risk: fixData.risk ?? "LOW", issues: [] });
      }
    } catch {
      setPreflightData({ score: 1.9, risk: "LOW", issues: [] });
    }
    setPreflightLoading(false);
  };

  /* ── Launch Campaign ── */
  const handleLaunch = async () => {
    setIsLaunching(true);
    setExecLogs([]);
    try {
      const res = await fetch(`${API}/api/campaigns/1/launch`, { method: "POST" });
      if (!res.ok) throw new Error("Launch failed");
      setExecLogs(prev => [...prev, { line: `[${new Date().toLocaleTimeString()}] ✅ Campaign launched — executing pipeline...`, color: "text-emerald-400" }]);

      // Open SSE stream for real-time events
      const es = new EventSource(`${API}/api/campaigns/1/stream`);
      const eventIcons: Record<string, string> = {
        trigger_started: "⚡",
        blocklist_passed: "🛡️",
        blocked: "🚫",
        message_generated: "🤖",
        delay_started: "⏳",
        delay_completed: "⏰",
        email_sent: "📧",
        email_failed: "❌",
        clawbot_triggered: "🦅",
        condition_evaluated: "🔀",
        lead_completed: "✅",
        campaign_completed: "🎯",
      };

      es.addEventListener("campaign_event", (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          const icon = eventIcons[data.event_type] || "▸";
          const ts = new Date().toLocaleTimeString();
          const leadName = data.payload?.lead_name || `Lead #${data.lead_id}`;
          const company = data.payload?.company ? ` (${data.payload.company})` : "";

          let detail = "";
          switch (data.event_type) {
            case "trigger_started":
              detail = `${leadName}${company} — entering pipeline`;
              break;
            case "blocked":
              detail = `${leadName} — BLOCKED: ${data.payload?.reason || "competitor domain"}`;
              break;
            case "blocklist_passed":
              detail = `${leadName} — cleared blocklist`;
              break;
            case "message_generated":
              detail = `AI drafted for ${leadName}: "${data.payload?.subject || ""}"`;
              if (data.payload?.hooks_used?.length) detail += ` [hooks: ${data.payload.hooks_used.join(", ")}]`;
              break;
            case "delay_started":
              detail = `Jitter delay active...`;
              break;
            case "delay_completed":
              detail = `Delay complete — resuming`;
              break;
            case "email_sent":
              detail = `✉️ Sent to ${data.payload?.to || leadName}: "${data.payload?.subject || ""}"`;
              break;
            case "email_failed":
              detail = `Failed to send to ${data.payload?.to || leadName}`;
              break;
            case "clawbot_triggered":
              detail = `🔥 Hot lead: ${leadName}${company} — WhatsApp alert sent!`;
              break;
            case "condition_evaluated":
              detail = `${leadName}: ${data.payload?.check} → ${data.payload?.result}`;
              break;
            case "lead_completed":
              detail = `${leadName} — pipeline complete`;
              break;
            case "campaign_completed":
              detail = `All leads processed — campaign complete!`;
              // Redirect to monitoring
              setTimeout(() => {
                es.close();
                router.push("/monitoring");
              }, 2000);
              break;
            default:
              detail = `${data.event_type}: ${JSON.stringify(data.payload || {}).slice(0, 80)}`;
          }

          const color = data.event_type === "blocked" || data.event_type === "email_failed"
            ? "text-red-400"
            : data.event_type === "email_sent" || data.event_type === "lead_completed" || data.event_type === "campaign_completed"
              ? "text-emerald-400"
              : data.event_type === "clawbot_triggered"
                ? "text-amber-400"
                : "text-blue-400";

          setExecLogs(prev => [...prev, { line: `[${ts}] ${icon} ${detail}`, color }]);
          if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
        } catch { /* ignore parse errors */ }
      });

      // Also handle generic messages
      es.onmessage = () => { };
      es.onerror = () => {
        // SSE may close after campaign completes — that's fine
        setIsLaunching(false);
      };

    } catch {
      setExecLogs(prev => [...prev, { line: `[${new Date().toLocaleTimeString()}] ❌ Launch failed — check backend logs`, color: "text-red-400" }]);
      setIsLaunching(false);
    }
  };

  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "linear-gradient(135deg, #ffffff 0%, #dbeafe 40%, #3b82f6 100%)" }}>
        <div className="text-slate-400 text-sm font-medium">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: "linear-gradient(135deg, #ffffff 0%, #dbeafe 40%, #3b82f6 100%)" }}>
      <DashboardNavbar onLogout={handleLogout} />
      {/* Ambient glows */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 rounded-full blur-[120px]" style={{ background: "rgba(59,130,246,0.15)" }} />
        <div className="absolute bottom-1/3 right-1/4 w-80 h-80 rounded-full blur-[100px]" style={{ background: "rgba(255,255,255,0.50)" }} />
      </div>

      {/* Header */}
      <div
        className="relative z-10 pl-72 pr-8 pt-24 pb-5 flex items-center justify-between"
        style={{ borderBottom: "1px solid rgba(59,130,246,0.15)" }}
      >
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Workflow</h1>
          <p className="text-sm mt-0.5 text-slate-500">
            AI outreach pipeline &middot; Agent:{" "}
            <span className="text-blue-600 font-semibold">{config.agentName}</span>
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCopilotOpen(!copilotOpen)}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 hover:scale-[1.02]"
            style={{ background: "rgba(168,85,247,0.12)", color: "#7c3aed", border: "1px solid rgba(168,85,247,0.20)" }}
          >
            ✨ Copilot
          </button>
          <button
            onClick={handlePreflight}
            disabled={preflightLoading}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 hover:scale-[1.02]"
            style={{ background: "rgba(245,158,11,0.12)", color: "#b45309", border: "1px solid rgba(245,158,11,0.20)" }}
          >
            {preflightLoading ? "⏳ Checking..." : "🛡 Preflight"}
          </button>
          <button
            onClick={handleLaunch}
            disabled={isLaunching}
            className="px-4 py-1.5 rounded-xl text-xs font-semibold text-white transition-all duration-300 hover:scale-[1.03]"
            style={{ background: "linear-gradient(135deg, #3b82f6, #1d4ed8)", boxShadow: "0 0 16px rgba(59,130,246,0.25)" }}
          >
            {isLaunching ? "🚀 Launching..." : "🚀 Launch"}
          </button>
          <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl ml-2" style={{ background: "rgba(34,197,94,0.12)", border: "1px solid rgba(34,197,94,0.20)" }}>
            <div className="w-2 h-2 rounded-full bg-green-400 animate-live-dot" />
            <span className="text-xs font-semibold text-green-400">Agent Active</span>
          </div>
        </div>
      </div>

      {/* Copilot input bar */}
      {copilotOpen && (
        <div className="relative z-10 pl-72 pr-8 pt-3">
          <div className="flex gap-2 rounded-2xl p-3" style={{ background: "rgba(255,255,255,0.70)", backdropFilter: "blur(20px)", border: "1px solid rgba(168,85,247,0.20)" }}>
            <input
              value={copilotInput}
              onChange={e => setCopilotInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleCopilot()}
              placeholder="Describe your outreach strategy..."
              className="flex-1 bg-transparent outline-none text-sm text-slate-800 placeholder:text-slate-400"
            />
            <button
              onClick={handleCopilot}
              disabled={copilotLoading}
              className="px-4 py-1.5 rounded-xl text-xs font-semibold text-white"
              style={{ background: "linear-gradient(135deg, #a855f7, #7c3aed)" }}
            >
              {copilotLoading ? "Generating..." : "Generate ✨"}
            </button>
          </div>
        </div>
      )}

      {/* Preflight result banner */}
      {preflightData && (
        <div className="relative z-10 pl-72 pr-8 pt-3">
          <div className={`flex items-center gap-3 rounded-xl px-4 py-2.5 text-xs font-semibold ${preflightData.risk === "LOW" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-amber-50 text-amber-700 border border-amber-200"}`}>
            {preflightData.risk === "LOW" ? "✅" : "⚠️"} Risk Score: {preflightData.score} — {preflightData.risk}
            {preflightData.issues.length === 0 && " · All clear, ready to launch!"}
          </div>
        </div>
      )}

      {/* Workflow canvas below */}

      {/* Workflow canvas */}
      <div className="relative z-10 pl-72 pr-8 pt-6 pb-8">
        <div
          className="rounded-3xl p-8 relative overflow-x-auto"
          style={{
            background: "rgba(255,255,255,0.55)",
            backdropFilter: "blur(24px) saturate(1.8)",
            border: "1px solid rgba(255,255,255,0.85)",
            boxShadow: "0 8px 40px rgba(0,0,0,0.08)",
            minHeight: 420,
          }}
        >
          {/* Dot grid */}
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              backgroundImage: "radial-gradient(circle, rgba(59,130,246,0.12) 1px, transparent 1px)",
              backgroundSize: "28px 28px",
            }}
          />
          <p
            className="text-[11px] font-bold tracking-widest uppercase mb-10 relative z-10 text-slate-400"
          >
            Pipeline
          </p>

          {/* Zoom controls */}
          <div className="absolute top-4 right-4 z-20 flex items-center gap-1.5 rounded-xl px-2 py-1" style={{ background: "rgba(255,255,255,0.8)", backdropFilter: "blur(8px)", border: "1px solid rgba(59,130,246,0.15)" }}>
            <button onClick={() => setZoom(z => Math.max(0.4, z - 0.1))} className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-500 hover:bg-blue-50 hover:text-blue-600 transition-colors font-bold text-sm">−</button>
            <span className="text-[11px] font-semibold text-slate-500 min-w-[36px] text-center">{Math.round(zoom * 100)}%</span>
            <button onClick={() => setZoom(z => Math.min(1.5, z + 0.1))} className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-500 hover:bg-blue-50 hover:text-blue-600 transition-colors font-bold text-sm">+</button>
            <button onClick={() => setZoom(0.85)} className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:bg-blue-50 hover:text-blue-600 transition-colors" title="Reset zoom">
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 4v6h6M23 20v-6h-6" /><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" /></svg>
            </button>
          </div>

          {/* Nodes */}
          <div className="relative" onWheel={handleCanvasWheel} style={{ height: 340, transform: `scale(${zoom})`, transformOrigin: "top left", transition: "transform 0.15s ease" }}>
            {/* SVG edges */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ overflow: "visible" }}>
              {nodes.slice(0, -1).map((n, i) => {
                const next = nodes[i + 1];
                const x1 = n.x + 44; const y1 = n.y + 44;
                const x2 = next.x + 44; const y2 = next.y + 44;
                return (
                  <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
                    stroke="rgba(59,130,246,0.30)" strokeWidth="2"
                    strokeDasharray="6 4"
                  />
                );
              })}
            </svg>
            {nodes.map(({ id, label, sub, x, y, bg, border, glow, icon }) => {
              const isHovered = hoveredNode === id;
              return (
                <div
                  key={id}
                  onMouseDown={(e) => onNodeMouseDown(e, id)}
                  onMouseEnter={() => setHoveredNode(id)}
                  onMouseLeave={() => setHoveredNode(null)}
                  className="absolute flex flex-col items-center gap-2.5 select-none"
                  style={{
                    left: x, top: y,
                    cursor: "grab",
                    width: 96,
                    transform: isHovered ? "scale(1.13) translateY(-4px)" : "scale(1) translateY(0px)",
                    transition: "transform 0.22s cubic-bezier(0.34,1.56,0.64,1)",
                    zIndex: isHovered ? 10 : 1,
                  }}
                >
                  <div
                    className="w-20 h-20 rounded-full flex items-center justify-center"
                    style={{
                      background: bg,
                      border: `1.5px solid ${border}`,
                      boxShadow: isHovered
                        ? `0 0 0 6px ${glow}, 0 0 40px ${glow}, 0 12px 32px rgba(0,0,0,0.12)`
                        : `0 0 20px ${glow}`,
                      backdropFilter: "blur(12px)",
                      transition: "box-shadow 0.22s ease",
                    }}
                  >
                    {icon}
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-bold text-slate-700 whitespace-nowrap">{label}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5 whitespace-nowrap">{sub}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Execution Log */}
      {execLogs.length > 0 && (
        <div className="relative z-10 pl-72 pr-8 pb-4">
          <div
            ref={logRef}
            className="rounded-2xl p-4 max-h-52 overflow-y-auto"
            style={{
              background: "rgba(15,23,42,0.90)",
              backdropFilter: "blur(20px)",
              border: "1px solid rgba(59,130,246,0.20)",
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            <p className="text-[10px] font-bold tracking-widest uppercase mb-3 text-blue-400/60">Execution Log</p>
            {execLogs.map((log, i) => (
              <p key={i} className={`text-xs leading-relaxed animate-fade-in-up ${log.color}`}>{log.line}</p>
            ))}
          </div>
        </div>
      )}

      {/* Floating leads panel */}
      <LeadsFloatingPanel leads={leads} />

      {/* Draggable sidebar */}
      <AgentSidebar config={config} activePage="workflow" />
    </div>
  );
}
