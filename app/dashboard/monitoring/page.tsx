"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Send,
  MailOpen,
  MessageSquare,
  CalendarCheck,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";

/* ── Stat Cards Data ── */
const stats = [
  { label: "Sent", value: "1,284", icon: Send, color: "violet", delta: "+12%" },
  { label: "Opened", value: "847", icon: MailOpen, color: "blue", delta: "+8.3%" },
  { label: "Replied", value: "156", icon: MessageSquare, color: "emerald", delta: "+23%" },
  { label: "Meetings Booked", value: "42", icon: CalendarCheck, color: "amber", delta: "+15%" },
];

const colorClasses: Record<string, { bg: string; text: string; glow: string }> = {
  violet: { bg: "bg-violet-500/15", text: "text-violet-400", glow: "shadow-[0_0_20px_rgba(139,92,246,0.15)]" },
  blue: { bg: "bg-blue-500/15", text: "text-blue-400", glow: "shadow-[0_0_20px_rgba(59,130,246,0.15)]" },
  emerald: { bg: "bg-emerald-500/15", text: "text-emerald-400", glow: "shadow-[0_0_20px_rgba(16,185,129,0.15)]" },
  amber: { bg: "bg-amber-500/15", text: "text-amber-400", glow: "shadow-[0_0_20px_rgba(245,158,11,0.15)]" },
};

/* ── Lead Table Data ── */
const leads = [
  { name: "Sarah Chen", company: "Acme Corp", stage: "Engaged", action: "Email opened", next: "Follow-up in 2d", status: "active" },
  { name: "James Wilson", company: "NextEra", stage: "Replied", action: "Replied positively", next: "Meeting invite", status: "active" },
  { name: "Priya Sharma", company: "StellarTech", stage: "Meeting", action: "Meeting booked", next: "Mar 8, 2pm", status: "booked" },
  { name: "Marcus Lee", company: "DataFlow AI", stage: "Cold", action: "No response", next: "Retry in 5d", status: "pending" },
  { name: "Elena Rodriguez", company: "CloudPeak", stage: "Engaged", action: "Link clicked", next: "Follow-up in 1d", status: "active" },
];

const stageBadgeColors: Record<string, string> = {
  Cold: "bg-white/[0.06] text-white/50 border-white/[0.08]",
  Engaged: "bg-violet-500/15 text-violet-300 border-violet-500/30",
  Replied: "bg-blue-500/15 text-blue-300 border-blue-500/30",
  Meeting: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
};

/* ── Heatmap Data ── */
function generateHeatmap() {
  const rows: string[][] = [];
  for (let r = 0; r < 2; r++) {
    const row: string[] = [];
    for (let c = 0; c < 48; c++) {
      const rand = Math.random();
      if (rand < 0.4) row.push("empty");
      else if (rand < 0.7) row.push("scheduled");
      else row.push("sent");
    }
    rows.push(row);
  }
  return rows;
}

const cellColor: Record<string, string> = {
  empty: "bg-white/[0.03]",
  scheduled: "bg-violet-500/40",
  sent: "bg-emerald-500/50",
};

/* ── Health Gauge ── */
function HealthGauge({ score }: { score: number }) {
  const circumference = 2 * Math.PI * 70;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative w-48 h-48 mx-auto">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 160 160">
        <circle
          cx="80"
          cy="80"
          r="70"
          fill="none"
          stroke="rgba(255,255,255,0.04)"
          strokeWidth="10"
        />
        <circle
          cx="80"
          cy="80"
          r="70"
          fill="none"
          stroke="url(#gauge-gradient)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000"
        />
        <defs>
          <linearGradient id="gauge-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#3b82f6" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-bold text-white">{score}</span>
        <span className="text-xs text-white/40">Health Score</span>
      </div>
    </div>
  );
}

export default function MonitoringDashboardPage() {
  const [safeMode, setSafeMode] = useState(false);
  const [campaign, setCampaign] = useState("q4-outreach");
  const heatmap = useMemo(() => generateHeatmap(), []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Monitoring</h1>
          <p className="text-sm text-white/50 mt-1">
            Real-time campaign performance
          </p>
        </div>
        <Select value={campaign} onValueChange={setCampaign}>
          <SelectTrigger className="w-[200px] bg-white/[0.04] border-white/[0.08] text-white">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-[#12121a] border-white/[0.1]">
            <SelectItem value="q4-outreach">Q4 Outreach</SelectItem>
            <SelectItem value="series-f-targets">Series F Targets</SelectItem>
            <SelectItem value="re-engagement">Re-engagement</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-4 gap-4">
        {stats.map(({ label, value, icon: Icon, color, delta }) => {
          const c = colorClasses[color];
          return (
            <Card
              key={label}
              className={`glass-strong rounded-2xl border-white/[0.08] ${c.glow}`}
            >
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className={`w-10 h-10 rounded-xl ${c.bg} flex items-center justify-center`}>
                    <Icon className={`w-5 h-5 ${c.text}`} />
                  </div>
                  <Badge
                    variant="outline"
                    className={`text-[10px] ${c.text} border-current/30`}
                  >
                    {delta}
                  </Badge>
                </div>
                <p className="text-2xl font-bold text-white">{value}</p>
                <p className="text-xs text-white/40 mt-0.5">{label}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Health Gauge + Safe Mode */}
      <div className="grid grid-cols-2 gap-4">
        <Card className="glass-strong rounded-2xl border-white/[0.08]">
          <CardContent className="p-6 flex flex-col items-center justify-center">
            <HealthGauge score={87} />
            <p className="text-xs text-white/40 mt-4 text-center">
              ChronoReach Health Score
            </p>
          </CardContent>
        </Card>

        <Card className="glass-strong rounded-2xl border-white/[0.08]">
          <CardContent className="p-6 flex flex-col items-center justify-center gap-6">
            <div
              className={`w-20 h-20 rounded-2xl flex items-center justify-center transition-all duration-300 ${
                safeMode
                  ? "bg-amber-500/15 shadow-[0_0_30px_rgba(245,158,11,0.2)]"
                  : "bg-emerald-500/15 shadow-[0_0_30px_rgba(16,185,129,0.2)]"
              }`}
            >
              {safeMode ? (
                <ShieldAlert className="w-10 h-10 text-amber-400" />
              ) : (
                <ShieldCheck className="w-10 h-10 text-emerald-400" />
              )}
            </div>
            <div className="text-center">
              <p className="text-lg font-semibold text-white">
                Safe Mode
              </p>
              <p className="text-xs text-white/40 mt-1">
                {safeMode
                  ? "All sends paused — manual approval required"
                  : "Automated sending active"}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Label className="text-sm text-white/50">OFF</Label>
              <Switch
                checked={safeMode}
                onCheckedChange={setSafeMode}
                className="data-[state=checked]:bg-amber-500"
              />
              <Label className="text-sm text-white/50">ON</Label>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Lead Table */}
      <Card className="glass-strong rounded-2xl border-white/[0.08] overflow-hidden">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-white/70">
            Lead Activity
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-white/[0.06] hover:bg-transparent">
                <TableHead className="text-white/40 text-xs">Name</TableHead>
                <TableHead className="text-white/40 text-xs">Company</TableHead>
                <TableHead className="text-white/40 text-xs">Stage</TableHead>
                <TableHead className="text-white/40 text-xs">
                  Last Action
                </TableHead>
                <TableHead className="text-white/40 text-xs">
                  Next Scheduled
                </TableHead>
                <TableHead className="text-white/40 text-xs">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {leads.map((lead, i) => (
                <TableRow
                  key={i}
                  className="border-white/[0.04] hover:bg-white/[0.02]"
                >
                  <TableCell className="text-sm text-white/80 font-medium">
                    {lead.name}
                  </TableCell>
                  <TableCell className="text-sm text-white/50">
                    {lead.company}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={stageBadgeColors[lead.stage] || ""}
                    >
                      {lead.stage}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-white/50">
                    {lead.action}
                  </TableCell>
                  <TableCell className="text-sm text-white/50">
                    {lead.next}
                  </TableCell>
                  <TableCell>
                    <span
                      className={`inline-flex items-center gap-1.5 text-xs ${
                        lead.status === "booked"
                          ? "text-emerald-400"
                          : lead.status === "active"
                            ? "text-violet-400"
                            : "text-white/30"
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          lead.status === "booked"
                            ? "bg-emerald-400"
                            : lead.status === "active"
                              ? "bg-violet-400 animate-pulse"
                              : "bg-white/20"
                        }`}
                      />
                      {lead.status}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Heatmap */}
      <Card className="glass-strong rounded-2xl border-white/[0.08]">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-white/70">
            Send Density Heatmap
          </CardTitle>
          <p className="text-[11px] text-white/30">
            48 × 30-min windows • Top: Today, Bottom: Yesterday
          </p>
        </CardHeader>
        <CardContent className="pb-4">
          <div className="space-y-1">
            {heatmap.map((row, ri) => (
              <div key={ri} className="flex gap-0.5">
                {row.map((cell, ci) => (
                  <div
                    key={ci}
                    className={`flex-1 h-5 rounded-sm ${cellColor[cell]} transition-colors`}
                    title={`${Math.floor(ci / 2)}:${ci % 2 === 0 ? "00" : "30"} — ${cell}`}
                  />
                ))}
              </div>
            ))}
          </div>
          <div className="flex items-center gap-4 mt-3 justify-end">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-sm bg-white/[0.03]" />
              <span className="text-[10px] text-white/30">Empty</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-sm bg-violet-500/40" />
              <span className="text-[10px] text-white/30">Scheduled</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-sm bg-emerald-500/50" />
              <span className="text-[10px] text-white/30">Sent</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
