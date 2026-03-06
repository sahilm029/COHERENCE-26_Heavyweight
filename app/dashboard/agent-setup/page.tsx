"use client";

import { useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Upload,
  Sparkles,
  ChevronRight,
  ChevronLeft,
  FileText,
  Ghost,
  Loader2,
  CheckCircle2,
} from "lucide-react";

const SLIDER_CONFIG = [
  { key: "tone", label: "Tone", description: "Casual → Formal" },
  { key: "aggression", label: "Aggression", description: "Soft → Pushy" },
  { key: "empathy", label: "Empathy", description: "Neutral → Warm" },
  { key: "ctaStyle", label: "CTA Style", description: "Subtle → Direct" },
] as const;

type SliderKey = (typeof SLIDER_CONFIG)[number]["key"];

const sampleEmails: Record<string, string[]> = {
  "1": [
    "Hey! Just saw your company is growing fast. Would love to chat sometime about how we could help.",
    "No worries if this isn't a fit — just thought I'd reach out since we're kind of in the same space.",
    "I totally get how hectic things can be during growth. Whenever you have a sec, I'd love to connect.",
    "If you're ever curious, happy to share some thoughts. No pressure at all!",
  ],
  "3": [
    "Hi — noticed your recent Series F. Congrats! We've helped similar companies scale outreach 3x.",
    "Would be great to connect and see if there's alignment. Let me know if a quick call works.",
    "I understand the demands of rapid scaling. We've seen teams like yours benefit significantly from automation.",
    "Would a brief demo make sense? Happy to walk you through our approach.",
  ],
  "5": [
    "Your Series F caught my attention. Companies at your stage lose $2M/yr to manual outreach — we fix that.",
    "I'm booking a slot for you this Thursday at 2pm. Confirm here or suggest another time.",
    "I've seen your exact pain points at 12 other Series F companies. Every day without us costs pipeline.",
    "Click here to book now. Our calendar fills fast and I'd hate for you to miss out.",
  ],
};

function getSampleEmail(sliders: Record<SliderKey, number>) {
  const avg = Math.round(
    Object.values(sliders).reduce((a, b) => a + b, 0) / 4
  );
  const level = avg <= 2 ? "1" : avg <= 4 ? "3" : "5";
  const emails = sampleEmails[level];
  return emails.map((line, i) => (
    <p key={i} className="text-sm text-white/70 leading-relaxed">
      {line}
    </p>
  ));
}

export default function AgentSetupPage() {
  const [step, setStep] = useState(1);
  const [avatarSeed, setAvatarSeed] = useState("agent");
  const [agentName, setAgentName] = useState("Ghost Agent");
  const [sliders, setSliders] = useState<Record<SliderKey, number>>({
    tone: 3,
    aggression: 2,
    empathy: 4,
    ctaStyle: 3,
  });
  const [ghostVoiceActive, setGhostVoiceActive] = useState(false);
  const [isActivating, setIsActivating] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);

  const generateAvatar = useCallback(() => {
    setAvatarSeed(`agent-${Date.now()}`);
  }, []);

  const activateGhostVoice = useCallback(() => {
    setIsActivating(true);
    setTimeout(() => {
      setIsActivating(false);
      setGhostVoiceActive(true);
    }, 2000);
  }, []);

  const handleFileDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const files = Array.from(e.dataTransfer.files).map((f) => f.name);
      setUploadedFiles((prev) => [...prev, ...files]);
    },
    []
  );

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-3rem)]">
      <div className="w-full max-w-2xl">
        {/* Step Indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center gap-2">
              <button
                onClick={() => setStep(s)}
                className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300 ${
                  step === s
                    ? "bg-violet-500 text-white shadow-[0_0_20px_rgba(139,92,246,0.4)]"
                    : step > s
                      ? "bg-violet-500/20 text-violet-300"
                      : "bg-white/[0.06] text-white/30"
                }`}
              >
                {step > s ? <CheckCircle2 className="w-4 h-4" /> : s}
              </button>
              {s < 3 && (
                <div
                  className={`w-16 h-0.5 rounded-full transition-colors ${
                    step > s ? "bg-violet-500/50" : "bg-white/[0.08]"
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        <Card className="glass-strong rounded-2xl border-white/[0.08] overflow-hidden">
          <CardContent className="p-8">
            {/* ═══ STEP 1: Avatar ═══ */}
            {step === 1 && (
              <div className="space-y-6 animate-in fade-in-0 slide-in-from-right-4 duration-300">
                <div>
                  <h2 className="text-xl font-bold text-white mb-1">
                    Create Your Agent
                  </h2>
                  <p className="text-sm text-white/50">
                    Upload or generate an avatar for your AI agent
                  </p>
                </div>

                <div className="flex flex-col items-center gap-6">
                  {/* Avatar Preview */}
                  <div className="relative group">
                    <div className="absolute -inset-1 rounded-full bg-gradient-to-r from-violet-500 to-blue-500 opacity-40 blur-md group-hover:opacity-60 transition-opacity" />
                    <Avatar className="relative w-28 h-28 border-2 border-white/10">
                      <AvatarImage
                        src={`https://api.dicebear.com/7.x/bottts/svg?seed=${avatarSeed}`}
                      />
                      <AvatarFallback className="bg-violet-500/20 text-violet-300 text-2xl">
                        AG
                      </AvatarFallback>
                    </Avatar>
                  </div>

                  {/* Upload Zone */}
                  <div
                    className="w-full border-2 border-dashed border-white/10 rounded-xl p-8 text-center hover:border-violet-500/30 hover:bg-violet-500/[0.03] transition-all cursor-pointer"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={handleFileDrop}
                  >
                    <Upload className="w-8 h-8 text-white/20 mx-auto mb-3" />
                    <p className="text-sm text-white/40">
                      Drag & drop an image, or click to browse
                    </p>
                  </div>

                  <div className="flex items-center gap-3 w-full">
                    <Input
                      value={agentName}
                      onChange={(e) => setAgentName(e.target.value)}
                      placeholder="Agent name"
                      className="flex-1 bg-white/[0.04] border-white/[0.08] text-white placeholder:text-white/30"
                    />
                    <Button
                      onClick={generateAvatar}
                      variant="outline"
                      className="shrink-0 border-violet-500/30 text-violet-300 hover:bg-violet-500/10"
                    >
                      <Sparkles className="w-4 h-4 mr-2" />
                      Generate Avatar
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* ═══ STEP 2: Personality Sliders ═══ */}
            {step === 2 && (
              <div className="space-y-6 animate-in fade-in-0 slide-in-from-right-4 duration-300">
                <div>
                  <h2 className="text-xl font-bold text-white mb-1">
                    Personality Tuning
                  </h2>
                  <p className="text-sm text-white/50">
                    Adjust sliders to shape your agent&apos;s communication
                    style
                  </p>
                </div>

                <div className="space-y-5">
                  {SLIDER_CONFIG.map(({ key, label, description }) => (
                    <div key={key} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm text-white/70">{label}</Label>
                        <span className="text-xs text-white/30">
                          {description}
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-white/30 w-4">1</span>
                        <Slider
                          value={[sliders[key]]}
                          onValueChange={([v]) =>
                            setSliders((p) => ({ ...p, [key]: v }))
                          }
                          min={1}
                          max={5}
                          step={1}
                          className="flex-1"
                        />
                        <span className="text-xs text-white/30 w-4">5</span>
                        <Badge
                          variant="outline"
                          className="w-8 justify-center border-violet-500/30 text-violet-300 bg-violet-500/10"
                        >
                          {sliders[key]}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Live Preview */}
                <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                  <p className="text-xs font-medium text-white/40 mb-3 uppercase tracking-wider">
                    Live Preview
                  </p>
                  <div className="space-y-2">
                    {getSampleEmail(sliders)}
                  </div>
                </div>
              </div>
            )}

            {/* ═══ STEP 3: Ghost Voice ═══ */}
            {step === 3 && (
              <div className="space-y-6 animate-in fade-in-0 slide-in-from-right-4 duration-300">
                <div>
                  <h2 className="text-xl font-bold text-white mb-1">
                    Ghost Voice Setup
                  </h2>
                  <p className="text-sm text-white/50">
                    Upload sample emails so the AI can match your writing style
                  </p>
                </div>

                {/* File Upload */}
                <div
                  className="border-2 border-dashed border-white/10 rounded-xl p-8 text-center hover:border-violet-500/30 hover:bg-violet-500/[0.03] transition-all cursor-pointer"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleFileDrop}
                >
                  <FileText className="w-8 h-8 text-white/20 mx-auto mb-3" />
                  <p className="text-sm text-white/40">
                    Drop .eml, .txt, or .csv files with sample emails
                  </p>
                  <p className="text-xs text-white/20 mt-1">
                    Minimum 5 emails recommended
                  </p>
                </div>

                {uploadedFiles.length > 0 && (
                  <div className="space-y-2">
                    {uploadedFiles.map((f, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.06]"
                      >
                        <FileText className="w-4 h-4 text-violet-400 shrink-0" />
                        <span className="text-sm text-white/70 truncate">
                          {f}
                        </span>
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 ml-auto shrink-0" />
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex items-center gap-3">
                  <Button
                    onClick={activateGhostVoice}
                    disabled={isActivating || ghostVoiceActive}
                    className="bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white"
                  >
                    {isActivating ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Ghost className="w-4 h-4 mr-2" />
                    )}
                    {isActivating
                      ? "Activating..."
                      : ghostVoiceActive
                        ? "Ghost Voice Active"
                        : "Activate Ghost Voice"}
                  </Button>
                  {ghostVoiceActive && (
                    <Badge className="bg-emerald-500/15 text-emerald-400 border-emerald-500/30 animate-in fade-in-0 zoom-in-95 duration-300">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse" />
                      ACTIVE
                    </Badge>
                  )}
                </div>
              </div>
            )}

            {/* Navigation */}
            <div className="flex items-center justify-between mt-8 pt-6 border-t border-white/[0.06]">
              <Button
                variant="ghost"
                onClick={() => setStep(Math.max(1, step - 1))}
                disabled={step === 1}
                className="text-white/50 hover:text-white"
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Back
              </Button>
              <Button
                onClick={() => setStep(Math.min(3, step + 1))}
                disabled={step === 3}
                className="bg-gradient-to-r from-violet-600 to-blue-600 text-white hover:from-violet-500 hover:to-blue-500"
              >
                Continue
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Agent Preview Card */}
        <Card className="mt-6 glass rounded-2xl border-white/[0.08] overflow-hidden animate-in fade-in-0 slide-in-from-bottom-2 duration-500">
          <CardContent className="p-5">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="absolute -inset-0.5 rounded-full bg-gradient-to-r from-violet-500 to-blue-500 opacity-50 blur-sm" />
                <Avatar className="relative w-12 h-12 border border-white/10">
                  <AvatarImage
                    src={`https://api.dicebear.com/7.x/bottts/svg?seed=${avatarSeed}`}
                  />
                  <AvatarFallback className="bg-violet-500/20 text-violet-300">
                    AG
                  </AvatarFallback>
                </Avatar>
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-white text-sm">{agentName}</p>
                <div className="flex items-center gap-3 mt-1.5">
                  {SLIDER_CONFIG.map(({ key, label }) => (
                    <div key={key} className="flex-1">
                      <p className="text-[10px] text-white/30 mb-1">{label}</p>
                      <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-violet-500 to-blue-500 transition-all duration-500"
                          style={{ width: `${(sliders[key] / 5) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              {ghostVoiceActive && (
                <Badge className="bg-emerald-500/15 text-emerald-400 border-emerald-500/30 shrink-0">
                  <Ghost className="w-3 h-3 mr-1" />
                  Ghost Voice: ACTIVE
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
