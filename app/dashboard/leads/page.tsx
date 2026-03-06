"use client";

import { useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Upload, CheckCircle2, FileSpreadsheet, ArrowRight } from "lucide-react";

const SAMPLE_LEADS = [
  {
    name: "Sarah Chen",
    email: "sarah@acmecorp.io",
    company: "Acme Corp",
    title: "VP Sales",
    insight: "Series F funding",
  },
  {
    name: "James Wilson",
    email: "j.wilson@nextera.com",
    company: "NextEra",
    title: "Head of Growth",
    insight: "Series F funding",
  },
  {
    name: "Priya Sharma",
    email: "priya@stellartech.io",
    company: "StellarTech",
    title: "CRO",
    insight: "Series F funding",
  },
  {
    name: "Marcus Lee",
    email: "marcus@dataflow.ai",
    company: "DataFlow AI",
    title: "Director BD",
    insight: "Series F funding",
  },
  {
    name: "Elena Rodriguez",
    email: "elena@cloudpeak.co",
    company: "CloudPeak",
    title: "CEO",
    insight: "Series F funding",
  },
];

const DETECTED_COLUMNS = [
  { detected: "full_name", label: "full_name" },
  { detected: "email_address", label: "email_address" },
  { detected: "org", label: "org" },
  { detected: "job_title", label: "job_title" },
  { detected: "funding_round", label: "funding_round" },
];

const STANDARD_FIELDS = [
  "Name",
  "Email",
  "Company",
  "Title",
  "Insight",
  "Phone",
  "LinkedIn",
  "Custom",
];

export default function LeadImportPage() {
  const [hasFile, setHasFile] = useState(false);
  const [mappings, setMappings] = useState<Record<string, string>>({
    full_name: "Name",
    email_address: "Email",
    org: "Company",
    job_title: "Title",
    funding_round: "Insight",
  });

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setHasFile(true);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Lead Import</h1>
        <p className="text-sm text-white/50 mt-1">
          Upload your lead list and map fields for campaign targeting
        </p>
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => setHasFile(true)}
        className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer ${
          hasFile
            ? "border-emerald-500/30 bg-emerald-500/[0.03]"
            : "border-white/10 hover:border-violet-500/30 hover:bg-violet-500/[0.02]"
        }`}
      >
        {hasFile ? (
          <div className="flex flex-col items-center gap-3 animate-in fade-in-0 zoom-in-95 duration-300">
            <div className="w-12 h-12 rounded-full bg-emerald-500/15 flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-white">
                leads_q4_2025.csv uploaded
              </p>
              <p className="text-xs text-white/40 mt-1">
                5 leads detected • 5 columns
              </p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-2xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center">
              <Upload className="w-7 h-7 text-white/20" />
            </div>
            <div>
              <p className="text-sm font-medium text-white/60">
                Drag & drop your CSV, XLS, or JSON file
              </p>
              <p className="text-xs text-white/30 mt-1">
                Or click to browse files
              </p>
            </div>
          </div>
        )}
      </div>

      {hasFile && (
        <div className="space-y-6 animate-in fade-in-0 slide-in-from-bottom-4 duration-500">
          {/* Data Table */}
          <Card className="glass-strong rounded-2xl border-white/[0.08] overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-white/70 flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-violet-400" />
                Preview Data
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="border-white/[0.06] hover:bg-transparent">
                    <TableHead className="text-white/40 text-xs">
                      Name
                    </TableHead>
                    <TableHead className="text-white/40 text-xs">
                      Email
                    </TableHead>
                    <TableHead className="text-white/40 text-xs">
                      Company
                    </TableHead>
                    <TableHead className="text-white/40 text-xs">
                      Title
                    </TableHead>
                    <TableHead className="text-white/40 text-xs">
                      Insight Badge
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {SAMPLE_LEADS.map((lead, i) => (
                    <TableRow
                      key={i}
                      className="border-white/[0.04] hover:bg-white/[0.02]"
                    >
                      <TableCell className="text-sm text-white/80 font-medium">
                        {lead.name}
                      </TableCell>
                      <TableCell className="text-sm text-white/50 font-mono">
                        {lead.email}
                      </TableCell>
                      <TableCell className="text-sm text-white/60">
                        {lead.company}
                      </TableCell>
                      <TableCell className="text-sm text-white/60">
                        {lead.title}
                      </TableCell>
                      <TableCell>
                        <Badge className="bg-violet-500/15 text-violet-300 border-violet-500/30 text-xs">
                          🚀 {lead.insight}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Field Mapping */}
          <Card className="glass rounded-2xl border-white/[0.08]">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-white/70">
                Field Mapping
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {DETECTED_COLUMNS.map(({ detected, label }) => (
                <div
                  key={detected}
                  className="flex items-center gap-4 p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]"
                >
                  <div className="flex-1">
                    <code className="text-xs bg-white/[0.06] px-2 py-1 rounded text-violet-300 font-mono">
                      {label}
                    </code>
                  </div>
                  <ArrowRight className="w-4 h-4 text-white/20 shrink-0" />
                  <div className="flex-1">
                    <Select
                      value={mappings[detected]}
                      onValueChange={(v) =>
                        setMappings((p) => ({ ...p, [detected]: v }))
                      }
                    >
                      <SelectTrigger className="bg-white/[0.04] border-white/[0.08] text-white text-sm h-9">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#12121a] border-white/[0.1]">
                        {STANDARD_FIELDS.map((f) => (
                          <SelectItem key={f} value={f}>
                            {f}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              ))}

              <div className="pt-4">
                <Button className="w-full bg-gradient-to-r from-violet-600 to-blue-600 text-white hover:from-violet-500 hover:to-blue-500">
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  Confirm Import &amp; Map Fields
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
