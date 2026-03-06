"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bot,
  Upload,
  GitBranch,
  BarChart3,
  Clock,
  FileBarChart,
  Zap,
} from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard/agent-setup", label: "Agent Setup", icon: Bot },
  { href: "/dashboard/leads", label: "Lead Import", icon: Upload },
  { href: "/dashboard/workflow", label: "Workflow Canvas", icon: GitBranch },
  { href: "/dashboard/monitoring", label: "Monitoring", icon: BarChart3 },
  { href: "/dashboard/replay", label: "Execution Replay", icon: Clock },
  { href: "/dashboard/autopsy", label: "Campaign Autopsy", icon: FileBarChart },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-[240px] z-40 flex flex-col border-r border-white/[0.06] bg-[#08080d]/90 backdrop-blur-xl">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/[0.06]">
        <Link href="/dashboard" className="flex items-center gap-2.5 group">
          <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-blue-500">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="text-lg font-bold tracking-tight text-white">
            ChronoReach
          </span>
        </Link>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-violet-500/15 text-white shadow-[0_0_12px_rgba(139,92,246,0.1)]"
                  : "text-white/50 hover:text-white/80 hover:bg-white/[0.04]"
              )}
            >
              <Icon
                className={cn(
                  "w-[18px] h-[18px] shrink-0",
                  isActive ? "text-violet-400" : "text-white/40"
                )}
              />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* ClawBot Status */}
      <div className="px-4 py-3 border-t border-white/[0.06]">
        <div className="flex items-center gap-2 px-2 py-2">
          <div className="relative">
            <Bot className="w-4 h-4 text-emerald-400" />
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
          </div>
          <span className="text-xs text-white/60">ClawBot</span>
          <Badge
            variant="outline"
            className="ml-auto text-[10px] px-1.5 py-0 border-emerald-500/30 text-emerald-400 bg-emerald-500/10"
          >
            Online
          </Badge>
        </div>
      </div>

      {/* Agent Mini Card */}
      <div className="px-4 pb-4">
        <div className="flex items-center gap-3 p-3 rounded-xl glass">
          <Avatar className="w-8 h-8 border border-white/10">
            <AvatarImage src="https://api.dicebear.com/7.x/bottts/svg?seed=agent" />
            <AvatarFallback className="bg-violet-500/20 text-violet-300 text-xs">
              AG
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-white truncate">
              Ghost Agent
            </p>
            <p className="text-[10px] text-white/40">Active</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
