"use client";

import { useState, useCallback, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Node,
  type Edge,
  Handle,
  Position,
  type NodeProps,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sparkles,
  Mic,
  Save,
  Play,
  Rocket,
  AlertTriangle,
  CheckCircle2,
  Wrench,
  ChevronDown,
  ChevronUp,
  Zap,
  Mail,
  Clock,
  GitBranch,
  ShieldBan,
  Bot,
  X,
  Activity,
} from "lucide-react";

/* ───── Custom Node ───── */
const colorMap: Record<string, { bg: string; border: string; icon: string }> = {
  trigger: { bg: "rgba(156,163,175,0.12)", border: "rgba(156,163,175,0.3)", icon: "#9ca3af" },
  ai_message: { bg: "rgba(139,92,246,0.12)", border: "rgba(139,92,246,0.3)", icon: "#8b5cf6" },
  send_email: { bg: "rgba(59,130,246,0.12)", border: "rgba(59,130,246,0.3)", icon: "#3b82f6" },
  delay: { bg: "rgba(245,158,11,0.12)", border: "rgba(245,158,11,0.3)", icon: "#f59e0b" },
  condition: { bg: "rgba(16,185,129,0.12)", border: "rgba(16,185,129,0.3)", icon: "#10b981" },
  blocklist: { bg: "rgba(239,68,68,0.12)", border: "rgba(239,68,68,0.3)", icon: "#ef4444" },
  clawbot: { bg: "rgba(249,115,22,0.12)", border: "rgba(249,115,22,0.3)", icon: "#f97316" },
};

const iconMap: Record<string, React.ComponentType<{ className?: string; style?: React.CSSProperties }>> = {
  trigger: Zap,
  ai_message: Sparkles,
  send_email: Mail,
  delay: Clock,
  condition: GitBranch,
  blocklist: ShieldBan,
  clawbot: Bot,
};

function WorkflowNode({ data }: NodeProps) {
  const nodeType = (data.nodeType as string) || "trigger";
  const colors = colorMap[nodeType] || colorMap.trigger;
  const Icon = iconMap[nodeType] || Zap;

  return (
    <div
      className="rounded-xl px-4 py-3 min-w-[160px] backdrop-blur-sm"
      style={{
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        boxShadow: `0 0 16px ${colors.bg}`,
      }}
    >
      <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-white/30 !border-0" />
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 shrink-0" style={{ color: colors.icon }} />
        <span className="text-sm font-medium text-white">{String(data.label)}</span>
      </div>
      {data.subtitle ? (
        <p className="text-[10px] text-white/40 mt-1 ml-6">{String(data.subtitle)}</p>
      ) : null}
      <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-white/30 !border-0" />
    </div>
  );
}

/* ───── Node Palette ───── */
const PALETTE = [
  { type: "trigger", label: "Trigger", color: "gray" },
  { type: "ai_message", label: "AI Message", color: "violet" },
  { type: "send_email", label: "Send Email", color: "blue" },
  { type: "delay", label: "Delay", color: "amber" },
  { type: "condition", label: "Condition", color: "green" },
  { type: "blocklist", label: "Blocklist", color: "red" },
  { type: "clawbot", label: "ClawBot Approval", color: "orange" },
];

/* ───── Default Nodes/Edges ───── */
const initialNodes: Node[] = [
  { id: "1", position: { x: 250, y: 50 }, data: { label: "New Lead Added", nodeType: "trigger", subtitle: "Webhook trigger" }, type: "workflow" },
  { id: "2", position: { x: 250, y: 180 }, data: { label: "Generate Email", nodeType: "ai_message", subtitle: "Ghost Voice" }, type: "workflow" },
  { id: "3", position: { x: 250, y: 310 }, data: { label: "Send Email", nodeType: "send_email", subtitle: "Primary sequence" }, type: "workflow" },
  { id: "4", position: { x: 250, y: 440 }, data: { label: "Wait 2 Days", nodeType: "delay", subtitle: "+jitter ±4h" }, type: "workflow" },
  { id: "5", position: { x: 100, y: 570 }, data: { label: "Replied?", nodeType: "condition" }, type: "workflow" },
  { id: "6", position: { x: 400, y: 570 }, data: { label: "ClawBot Review", nodeType: "clawbot", subtitle: "Approval required" }, type: "workflow" },
];

const initialEdges: Edge[] = [
  { id: "e1-2", source: "1", target: "2", animated: true, style: { stroke: "rgba(139,92,246,0.4)" } },
  { id: "e2-3", source: "2", target: "3", animated: true, style: { stroke: "rgba(59,130,246,0.4)" } },
  { id: "e3-4", source: "3", target: "4", style: { stroke: "rgba(245,158,11,0.4)" } },
  { id: "e4-5", source: "4", target: "5", style: { stroke: "rgba(16,185,129,0.4)" } },
  { id: "e4-6", source: "4", target: "6", style: { stroke: "rgba(249,115,22,0.4)" } },
];

/* ───── Preflight Issues ───── */
const PREFLIGHT_ISSUES = [
  { severity: "warning", text: "No blocklist node — potential compliance risk", fixable: true },
  { severity: "info", text: "Delay jitter is low (+4h). Recommend ±8h for realism", fixable: true },
  { severity: "ok", text: "Ghost Voice calibrated", fixable: false },
  { severity: "ok", text: "Lead list verified (5 leads)", fixable: false },
];

/* ───── Execution Logs ───── */
const EXEC_LOGS = [
  "[00:00.000] Workflow engine initialized",
  "[00:00.012] Loading nodes... 6 nodes found",
  "[00:00.024] Validating edges... 5 connections OK",
  "[00:00.051] Preflight check PASSED (score: 82/100)",
  '[00:00.102] Trigger "New Lead Added" armed',
  "[00:01.340] → Lead ingested: sarah@acmecorp.io",
  '[00:01.892] AI Message generating with Ghost Voice...',
  "[00:03.401] ✓ Email generated (tone: 3, empathy: 4)",
  "[00:03.450] Queued for send: sarah@acmecorp.io",
  "[00:03.501] Delay node: waiting 2d +jitter(3h22m)",
];

export default function WorkflowCanvasPage() {
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [preflightOpen, setPreflightOpen] = useState(false);
  const [logOpen, setLogOpen] = useState(true);

  const nodeTypes = useMemo(() => ({ workflow: WorkflowNode }), []);

  const onConnect = useCallback(
    (params: Connection) =>
      setEdges((eds) =>
        addEdge(
          { ...params, animated: true, style: { stroke: "rgba(139,92,246,0.4)" } },
          eds,
        ),
      ),
    [setEdges],
  );

  const onDragStart = useCallback(
    (e: React.DragEvent, nodeType: string, label: string) => {
      e.dataTransfer.setData("application/reactflow-type", nodeType);
      e.dataTransfer.setData("application/reactflow-label", label);
      e.dataTransfer.effectAllowed = "move";
    },
    [],
  );

  return (
    <div className="flex h-[calc(100vh-3rem)] -m-6 relative">
      {/* ── Left: Node Palette ── */}
      <div className="w-[240px] shrink-0 border-r border-white/[0.06] bg-[#08080d]/60 backdrop-blur-xl p-4 flex flex-col">
        <h3 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-4">
          Node Palette
        </h3>
        <div className="space-y-2">
          {PALETTE.map(({ type, label }) => {
            const colors = colorMap[type] || colorMap.trigger;
            const Icon = iconMap[type] || Zap;
            return (
              <div
                key={type}
                draggable
                onDragStart={(e) => onDragStart(e, type, label)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-grab active:cursor-grabbing transition-all hover:scale-[1.02]"
                style={{
                  background: colors.bg,
                  border: `1px solid ${colors.border}`,
                }}
              >
                <Icon className="w-4 h-4 shrink-0" style={{ color: colors.icon }} />
                <span className="text-sm text-white/80">{label}</span>
              </div>
            );
          })}
        </div>

        {/* Behavioral Pulse */}
        <div className="mt-auto pt-4">
          <Card className="glass rounded-xl border-white/[0.06]">
            <CardHeader className="p-3 pb-2">
              <CardTitle className="text-[11px] font-medium text-white/40 uppercase tracking-wider flex items-center gap-1.5">
                <Activity className="w-3 h-3 text-violet-400" />
                Behavioral Pulse
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 pt-0 space-y-2.5">
              {[
                { label: "Send Velocity", value: 72, color: "from-violet-500 to-blue-500" },
                { label: "Active Window", value: 85, color: "from-blue-500 to-cyan-500" },
                { label: "Last Jitter", value: 45, color: "from-amber-500 to-orange-500" },
              ].map(({ label, value, color }) => (
                <div key={label}>
                  <div className="flex justify-between mb-1">
                    <span className="text-[10px] text-white/40">{label}</span>
                    <span className="text-[10px] text-white/60">{value}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                    <div
                      className={`h-full rounded-full bg-gradient-to-r ${color} transition-all duration-1000`}
                      style={{ width: `${value}%` }}
                    />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* ── Center: Canvas ── */}
      <div className="flex-1 relative flex flex-col">
        {/* Top Bar */}
        <div className="h-12 border-b border-white/[0.06] bg-[#0a0a0f]/80 backdrop-blur-lg px-4 flex items-center gap-2 shrink-0">
          <Button
            size="sm"
            variant="outline"
            className="border-violet-500/30 text-violet-300 hover:bg-violet-500/10 h-8 text-xs"
          >
            <Sparkles className="w-3.5 h-3.5 mr-1.5" />
            Campaign Copilot
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="border-white/10 text-white/50 hover:bg-white/[0.04] h-8 w-8 p-0"
          >
            <Mic className="w-3.5 h-3.5" />
          </Button>
          <div className="flex-1" />
          <Button
            size="sm"
            variant="outline"
            className="border-white/10 text-white/60 h-8 text-xs"
          >
            <Save className="w-3.5 h-3.5 mr-1.5" />
            Save
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="border-amber-500/30 text-amber-300 hover:bg-amber-500/10 h-8 text-xs"
            onClick={() => setPreflightOpen(true)}
          >
            <Play className="w-3.5 h-3.5 mr-1.5" />
            Run Preflight
          </Button>
          <Button
            size="sm"
            className="bg-gradient-to-r from-violet-600 to-blue-600 text-white h-8 text-xs"
          >
            <Rocket className="w-3.5 h-3.5 mr-1.5" />
            Launch
          </Button>
        </div>

        {/* ReactFlow Canvas */}
        <div className="flex-1 relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            fitView
            className="!bg-transparent"
          >
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="rgba(255,255,255,0.04)" />
            <Controls
              className="!bg-white/[0.04] !border-white/[0.08] !rounded-xl [&>button]:!bg-transparent [&>button]:!border-white/[0.08] [&>button]:!text-white/40 [&>button:hover]:!bg-white/[0.06]"
            />
          </ReactFlow>
        </div>

        {/* Bottom: Execution Log */}
        <div
          className={`border-t border-white/[0.06] bg-[#08080d]/90 backdrop-blur-xl transition-all duration-300 ${
            logOpen ? "h-[180px]" : "h-9"
          }`}
        >
          <button
            onClick={() => setLogOpen(!logOpen)}
            className="flex items-center gap-2 px-4 h-9 w-full text-left"
          >
            <span className="text-[11px] font-medium text-white/40 uppercase tracking-wider">
              Execution Log
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <div className="flex-1" />
            {logOpen ? (
              <ChevronDown className="w-3.5 h-3.5 text-white/30" />
            ) : (
              <ChevronUp className="w-3.5 h-3.5 text-white/30" />
            )}
          </button>
          {logOpen && (
            <ScrollArea className="h-[calc(100%-36px)] px-4 pb-2">
              <div className="font-mono text-xs space-y-0.5">
                {EXEC_LOGS.map((line, i) => (
                  <p
                    key={i}
                    className={`${
                      line.includes("✓")
                        ? "text-emerald-400/80"
                        : line.includes("→")
                          ? "text-violet-400/80"
                          : "text-white/30"
                    }`}
                  >
                    {line}
                  </p>
                ))}
              </div>
            </ScrollArea>
          )}
        </div>
      </div>

      {/* ── Right: Preflight Panel ── */}
      <div
        className={`absolute top-0 right-0 bottom-0 w-[320px] border-l border-white/[0.06] bg-[#08080d]/95 backdrop-blur-xl z-20 transition-transform duration-300 ${
          preflightOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="p-4 border-b border-white/[0.06] flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">
            Preflight Results
          </h3>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setPreflightOpen(false)}
            className="w-7 h-7 p-0 text-white/40 hover:text-white"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="p-4 space-y-4">
          {/* Risk Score */}
          <div className="flex items-center gap-3 p-3 rounded-xl glass">
            <div className="w-12 h-12 rounded-lg bg-amber-500/15 flex items-center justify-center">
              <span className="text-lg font-bold text-amber-400">82</span>
            </div>
            <div>
              <p className="text-sm font-medium text-white">Risk Score</p>
              <Badge
                variant="outline"
                className="border-amber-500/30 text-amber-300 bg-amber-500/10 text-[10px] mt-0.5"
              >
                Medium
              </Badge>
            </div>
          </div>

          {/* Issues */}
          <div className="space-y-2">
            {PREFLIGHT_ISSUES.map((issue, i) => (
              <div
                key={i}
                className="flex items-start gap-2.5 p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]"
              >
                {issue.severity === "warning" ? (
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                ) : issue.severity === "info" ? (
                  <AlertTriangle className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                )}
                <p className="text-xs text-white/60 flex-1">{issue.text}</p>
                {issue.fixable && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-6 px-2 text-[10px] text-violet-300 hover:bg-violet-500/10"
                  >
                    <Wrench className="w-3 h-3 mr-1" />
                    Fix
                  </Button>
                )}
              </div>
            ))}
          </div>

          <Button className="w-full bg-gradient-to-r from-violet-600 to-blue-600 text-white text-sm">
            <Wrench className="w-4 h-4 mr-2" />
            Fix All Issues
          </Button>
        </div>
      </div>
    </div>
  );
}
