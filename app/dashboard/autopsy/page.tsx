"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Send,
  MailOpen,
  MessageSquare,
  CalendarCheck,
  MousePointerClick,
  Clock,
  ShieldBan,
  TrendingUp,
  Users,
  Zap,
  Share2,
  Download,
} from "lucide-react";

const METRICS = [
  { label: "Total Sent", value: "1,284", icon: Send, color: "text-violet-400", bg: "bg-violet-500/15" },
  { label: "Total Opened", value: "847", icon: MailOpen, color: "text-blue-400", bg: "bg-blue-500/15" },
  { label: "Open Rate", value: "65.9%", icon: TrendingUp, color: "text-cyan-400", bg: "bg-cyan-500/15" },
  { label: "Replies", value: "156", icon: MessageSquare, color: "text-emerald-400", bg: "bg-emerald-500/15" },
  { label: "Reply Rate", value: "12.1%", icon: TrendingUp, color: "text-emerald-400", bg: "bg-emerald-500/15" },
  { label: "Meetings Booked", value: "42", icon: CalendarCheck, color: "text-amber-400", bg: "bg-amber-500/15" },
  { label: "Click-throughs", value: "312", icon: MousePointerClick, color: "text-pink-400", bg: "bg-pink-500/15" },
  { label: "Avg. Response Time", value: "4.2h", icon: Clock, color: "text-orange-400", bg: "bg-orange-500/15" },
  { label: "Bounce Rate", value: "1.8%", icon: ShieldBan, color: "text-red-400", bg: "bg-red-500/15" },
  { label: "Conversion Rate", value: "3.3%", icon: Zap, color: "text-violet-400", bg: "bg-violet-500/15" },
  { label: "Leads Engaged", value: "423", icon: Users, color: "text-blue-400", bg: "bg-blue-500/15" },
  { label: "Ghost Voice Accuracy", value: "94%", icon: Zap, color: "text-emerald-400", bg: "bg-emerald-500/15" },
];

export default function CampaignAutopsyPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Campaign Autopsy</h1>
        <p className="text-sm text-white/50 mt-1">
          Complete performance analysis — Q4 Outreach Campaign
        </p>
      </div>

      {/* Main Card with Gradient Border */}
      <div className="relative rounded-2xl p-px bg-gradient-to-br from-violet-500/40 via-blue-500/20 to-pink-500/30">
        <Card className="rounded-2xl bg-[#0a0a0f]/95 backdrop-blur-xl border-0">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg text-white">
                  Q4 Outreach — Final Report
                </CardTitle>
                <p className="text-xs text-white/40 mt-1">
                  Campaign ran: Feb 15 – Mar 5, 2026 • 18 days
                </p>
              </div>
              <Badge
                variant="outline"
                className="border-emerald-500/30 text-emerald-400 bg-emerald-500/10"
              >
                Completed
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* 3x4 Metrics Grid */}
            <div className="grid grid-cols-4 gap-3">
              {METRICS.map(({ label, value, icon: Icon, color, bg }) => (
                <div
                  key={label}
                  className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] hover:bg-white/[0.04] transition-colors"
                >
                  <div className="flex items-center gap-2 mb-2.5">
                    <div
                      className={`w-8 h-8 rounded-lg ${bg} flex items-center justify-center`}
                    >
                      <Icon className={`w-4 h-4 ${color}`} />
                    </div>
                  </div>
                  <p className="text-xl font-bold text-white">{value}</p>
                  <p className="text-[11px] text-white/40 mt-0.5">{label}</p>
                </div>
              ))}
            </div>

            <Separator className="bg-white/[0.06]" />

            {/* Human Time Saved */}
            <div className="relative overflow-hidden rounded-xl p-6 text-center">
              {/* Gradient background */}
              <div className="absolute inset-0 bg-gradient-to-r from-violet-500/10 via-blue-500/10 to-violet-500/10" />
              <div className="absolute inset-0 backdrop-blur-sm" />
              <div className="relative z-10">
                <p className="text-sm text-white/50 mb-2">
                  Estimated human time saved
                </p>
                <p className="text-5xl font-bold bg-gradient-to-r from-violet-400 via-blue-400 to-violet-400 bg-clip-text text-transparent">
                  8.5 hours
                </p>
                <p className="text-xs text-white/30 mt-2">
                  Based on avg. 4 min/email × 1,284 sends + research time
                </p>
              </div>
            </div>

            <Separator className="bg-white/[0.06]" />

            {/* Actions */}
            <div className="flex items-center justify-end gap-3">
              <Button
                variant="outline"
                className="border-white/10 text-white/60 hover:bg-white/[0.04]"
              >
                <Share2 className="w-4 h-4 mr-2" />
                Share Report
              </Button>
              <Button className="bg-gradient-to-r from-violet-600 to-blue-600 text-white hover:from-violet-500 hover:to-blue-500">
                <Download className="w-4 h-4 mr-2" />
                Export PDF
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
