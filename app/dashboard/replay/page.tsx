"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Mail,
  Sparkles,
  Clock,
  CalendarCheck,
  ShieldBan,
  AlertTriangle,
  ChevronDown,
  Send,
  Eye,
} from "lucide-react";

type TimelineEvent = {
  id: number;
  type: "ai_message" | "send" | "delay" | "open" | "reply" | "meeting" | "blocklist" | "warning";
  time: string;
  title: string;
  description: string;
  reasons?: string[];
  jitter?: string;
};

const EVENTS: TimelineEvent[] = [
  {
    id: 1,
    type: "meeting",
    time: "Mar 6, 2:15 PM",
    title: "Meeting Booked",
    description: "Priya Sharma confirmed meeting — Mar 8 at 2:00 PM",
  },
  {
    id: 2,
    type: "reply",
    time: "Mar 6, 11:42 AM",
    title: "Reply Received",
    description: 'James Wilson replied: "Sounds great, let\'s connect!"',
  },
  {
    id: 3,
    type: "open",
    time: "Mar 6, 10:05 AM",
    title: "Email Opened",
    description: "Sarah Chen opened email (3rd open)",
  },
  {
    id: 4,
    type: "send",
    time: "Mar 6, 9:31 AM",
    title: "Email Sent",
    description: "Follow-up #2 sent to elena@cloudpeak.co",
  },
  {
    id: 5,
    type: "delay",
    time: "Mar 6, 9:08 AM",
    title: "Delay Completed",
    description: "2-day delay finished for Sarah Chen sequence",
    jitter: "+23 min applied",
  },
  {
    id: 6,
    type: "ai_message",
    time: "Mar 5, 3:45 PM",
    title: "AI Message Generated",
    description: "Ghost Voice composed email for Marcus Lee — tone: warm, CTA: soft",
    reasons: ["funding_stage", "linkedin_headline", "company_size", "recent_hiring"],
  },
  {
    id: 7,
    type: "blocklist",
    time: "Mar 5, 2:12 PM",
    title: "Blocklist Match",
    description: "skip@blocked-domain.com filtered out — domain on global blocklist",
  },
  {
    id: 8,
    type: "ai_message",
    time: "Mar 5, 11:20 AM",
    title: "AI Message Generated",
    description: "Initial outreach crafted for Sarah Chen — using Series F context",
    reasons: ["funding_stage", "job_title", "tech_stack"],
  },
  {
    id: 9,
    type: "warning",
    time: "Mar 5, 10:00 AM",
    title: "Rate Limit Warning",
    description: "Send velocity approaching provider threshold — auto-throttled",
  },
  {
    id: 10,
    type: "send",
    time: "Mar 5, 9:15 AM",
    title: "Campaign Launched",
    description: "Q4 Outreach campaign started — 5 leads queued",
  },
];

const typeConfig: Record<
  string,
  { borderColor: string; bgColor: string; icon: React.ComponentType<{ className?: string }>; iconColor: string }
> = {
  ai_message: { borderColor: "border-l-violet-500", bgColor: "", icon: Sparkles, iconColor: "text-violet-400" },
  send: { borderColor: "border-l-blue-500", bgColor: "", icon: Send, iconColor: "text-blue-400" },
  delay: { borderColor: "border-l-amber-500", bgColor: "", icon: Clock, iconColor: "text-amber-400" },
  open: { borderColor: "border-l-cyan-500", bgColor: "", icon: Eye, iconColor: "text-cyan-400" },
  reply: { borderColor: "border-l-blue-400", bgColor: "", icon: Mail, iconColor: "text-blue-300" },
  meeting: { borderColor: "border-l-emerald-500", bgColor: "bg-emerald-500/[0.04]", icon: CalendarCheck, iconColor: "text-emerald-400" },
  blocklist: { borderColor: "border-l-red-500", bgColor: "", icon: ShieldBan, iconColor: "text-red-400" },
  warning: { borderColor: "border-l-amber-400", bgColor: "bg-amber-500/[0.03]", icon: AlertTriangle, iconColor: "text-amber-400" },
};

function TimelineCard({ event }: { event: TimelineEvent }) {
  const [expanded, setExpanded] = useState(false);
  const config = typeConfig[event.type] || typeConfig.send;
  const Icon = config.icon;

  return (
    <div className="flex gap-4">
      {/* Timeline line + dot */}
      <div className="flex flex-col items-center">
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 glass ${
            event.type === "meeting" ? "bg-emerald-500/15" : ""
          }`}
        >
          <Icon className={`w-4 h-4 ${config.iconColor}`} />
        </div>
        <div className="w-px flex-1 bg-white/[0.06] min-h-4" />
      </div>

      {/* Card */}
      <Card
        className={`flex-1 mb-3 glass rounded-xl border-white/[0.06] border-l-2 ${config.borderColor} ${config.bgColor} overflow-hidden`}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-white">{event.title}</p>
              <p className="text-xs text-white/50 mt-1">{event.description}</p>
            </div>
            <span className="text-[10px] text-white/30 whitespace-nowrap shrink-0">
              {event.time}
            </span>
          </div>

          {/* Jitter info */}
          {event.jitter && (
            <div className="mt-2">
              <Badge
                variant="outline"
                className="border-amber-500/30 text-amber-300 bg-amber-500/10 text-[10px]"
              >
                <Clock className="w-3 h-3 mr-1" />
                Jitter: {event.jitter}
              </Badge>
            </div>
          )}

          {/* AI reasons expandable */}
          {event.reasons && (
            <div className="mt-2">
              <button
                onClick={() => setExpanded(!expanded)}
                className="flex items-center gap-1.5 text-[11px] text-violet-400 hover:text-violet-300 transition-colors"
              >
                <ChevronDown
                  className={`w-3 h-3 transition-transform duration-200 ${
                    expanded ? "rotate-180" : ""
                  }`}
                />
                Why this message?
              </button>
              {expanded && (
                <div className="flex flex-wrap gap-1.5 mt-2 animate-in fade-in-0 slide-in-from-top-1 duration-200">
                  <span className="text-[10px] text-white/30">Used:</span>
                  {event.reasons.map((r) => (
                    <Badge
                      key={r}
                      variant="outline"
                      className="text-[10px] border-violet-500/20 text-violet-300 bg-violet-500/10"
                    >
                      {r}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function ExecutionReplayPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Execution Replay</h1>
        <p className="text-sm text-white/50 mt-1">
          Timeline of all campaign events — newest first
        </p>
      </div>

      <div className="max-w-3xl">
        {EVENTS.map((event) => (
          <TimelineCard key={event.id} event={event} />
        ))}

        {/* Timeline end */}
        <div className="flex gap-4">
          <div className="flex flex-col items-center">
            <div className="w-8 h-8 rounded-full flex items-center justify-center bg-white/[0.04] border border-white/[0.08]">
              <div className="w-2 h-2 rounded-full bg-white/20" />
            </div>
          </div>
          <div className="pt-1.5">
            <p className="text-xs text-white/20">Campaign start</p>
          </div>
        </div>
      </div>
    </div>
  );
}
