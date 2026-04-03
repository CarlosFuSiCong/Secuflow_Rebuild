"use client";

import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import Card from "@/components/horizon/Card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Users,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  FileCode,
  ArrowRight,
  BarChart3,
  AlertCircle,
  Loader2,
} from "lucide-react";
import * as mcstcApi from "@/lib/api/mcstc";
import * as stcApi from "@/lib/api/stc";
import type { CoordinationPair } from "@/lib/api/mcstc";
import type { STCResult } from "@/lib/api/stc";

interface CoordinationPairsModalProps {
  stcId?: string;
  mcstcId?: string;
  branch: string;
  open: boolean;
  onClose: () => void;
}

// ─── Shared helpers ────────────────────────────────────────────────────────────

function StatusBadge({ pair }: { pair: CoordinationPair }) {
  if (pair.is_missed_coordination) {
    return (
      <span className="inline-flex items-center gap-1 text-xs border rounded px-1.5 py-0.5 bg-transparent text-red-600 border-red-300">
        <AlertTriangle className="h-3 w-3" />
        Missed
      </span>
    );
  }
  if (pair.is_unnecessary_coordination) {
    return (
      <span className="inline-flex items-center gap-1 text-xs border rounded px-1.5 py-0.5 bg-transparent text-orange-600 border-orange-300">
        <XCircle className="h-3 w-3" />
        Unnecessary
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-xs border rounded px-1.5 py-0.5 bg-transparent text-green-600 border-green-300">
      <CheckCircle className="h-3 w-3" />
      Adequate
    </span>
  );
}

function RoleTag({ role }: { role: string }) {
  return (
    <span className="text-xs border rounded px-1.5 py-0.5 bg-transparent border-border text-muted-foreground capitalize">
      {role}
    </span>
  );
}

function MetricRow({
  label,
  value,
  sub,
  icon,
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-border last:border-0">
      <div className="flex items-center gap-2">
        {icon && <span className="text-muted-foreground">{icon}</span>}
        <div>
          <p className="text-sm font-medium">{label}</p>
          {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
        </div>
      </div>
      <span className="text-sm font-semibold tabular-nums">{value}</span>
    </div>
  );
}

// ─── Main component ────────────────────────────────────────────────────────────

export function CoordinationPairsModal({
  stcId,
  mcstcId,
  branch,
  open,
  onClose,
}: CoordinationPairsModalProps) {
  const [activeTab, setActiveTab] = useState<"stc" | "mcstc">("stc");
  const [pairs, setPairs] = useState<CoordinationPair[]>([]);
  const [stcResult, setStcResult] = useState<STCResult | null>(null);
  const [mcstcResult, setMcstcResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [topN, setTopN] = useState<number>(10);

  useEffect(() => {
    if (open) {
      setActiveTab(mcstcId && !stcId ? "mcstc" : "stc");
    }
  }, [open, stcId, mcstcId]);

  useEffect(() => {
    if (!open) return;
    if (activeTab === "stc" && stcId) fetchSTCResult();
    else if (activeTab === "mcstc" && mcstcId) fetchMCSTCData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, activeTab, stcId, mcstcId, statusFilter, topN]);

  const fetchSTCResult = async () => {
    if (!stcId) return;
    setLoading(true);
    setError(null);
    try {
      setStcResult(await stcApi.getSTCResults(stcId));
    } catch {
      setError("Failed to load STC data");
    } finally {
      setLoading(false);
    }
  };

  const fetchMCSTCData = async () => {
    if (!mcstcId) return;
    setLoading(true);
    setError(null);
    try {
      const [pairsResult, mcstcRes] = await Promise.all([
        mcstcApi.getCoordinationPairs(mcstcId, {
          topN,
          statusFilter: statusFilter === "all" ? undefined : (statusFilter as any),
        }),
        mcstcApi.getMCSTCResults(mcstcId),
      ]);
      setPairs(pairsResult.coordination_pairs);
      setMcstcResult(mcstcRes);
    } catch (err: any) {
      setError("Failed to load MC-STC data: " + (err.response?.data?.message || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl overflow-hidden p-0">
        {/* Scrollable inner wrapper keeps border-radius intact on both sides */}
        <div className="max-h-[90vh] overflow-y-auto p-6">
        <DialogHeader className="pr-8">
          <DialogTitle className="flex items-center gap-2 text-base font-semibold tracking-tight">
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
            Analysis Details
            <span className="text-muted-foreground font-normal">— {branch}</span>
          </DialogTitle>
        </DialogHeader>

        {/* Tab Navigation */}
        <div className="flex items-center gap-6 border-b border-border -mt-2">
          {stcId && (
            <button
              onClick={() => setActiveTab("stc")}
              className={`pb-2 text-sm transition-colors border-b-2 -mb-px ${
                activeTab === "stc"
                  ? "border-foreground text-foreground font-medium"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              STC Analysis
            </button>
          )}
          {mcstcId && (
            <button
              onClick={() => setActiveTab("mcstc")}
              className={`pb-2 text-sm transition-colors border-b-2 -mb-px ${
                activeTab === "mcstc"
                  ? "border-foreground text-foreground font-medium"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              MC-STC Analysis
            </button>
          )}
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center gap-2 py-16 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-xs">Loading analysis data...</span>
          </div>
        ) : error ? (
          <div className="py-12 text-center text-sm text-destructive">{error}</div>
        ) : (
          <>
            {activeTab === "stc" && stcResult && renderSTCContent()}
            {activeTab === "mcstc" && mcstcResult && renderMCSTCContent()}
          </>
        )}
        </div>
      </DialogContent>
    </Dialog>
  );

  // ─── STC content ──────────────────────────────────────────────────────────────

  function renderSTCContent() {
    if (!stcResult) return null;
    const r = stcResult.results;
    const stcPct = ((1 - r.stc_value) * 100).toFixed(1);
    const effPct = (r.coordination_efficiency * 100).toFixed(1);

    return (
      <div className="space-y-6 pt-2">
        {/* Overview grid */}
        <Card className="p-5">
          <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground mb-4">
            Overview
          </p>
          <div className="grid grid-cols-2 gap-x-8 gap-y-4">
            <div>
              <p className="text-xs text-muted-foreground">Branch</p>
              <p className="text-sm font-medium mt-0.5">{r.branch_analyzed || "—"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Analysis Date</p>
              <p className="text-sm font-medium mt-0.5">
                {new Date(stcResult.analysis_date).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Contributors</p>
              <p className="text-sm font-medium mt-0.5">{r.contributors_count}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Files Analyzed</p>
              <p className="text-sm font-medium mt-0.5">{r.files_count}</p>
            </div>
          </div>
        </Card>

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-4">
          <Card className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted-foreground mb-1">STC Value</p>
                <p className={`text-2xl font-semibold tracking-tight ${(1 - r.stc_value) > 0.7 ? "text-green-600" : (1 - r.stc_value) > 0.3 ? "text-orange-600" : "text-red-600"}`}>
                  {((1 - r.stc_value) * 100).toFixed(1)}%
                </p>
              </div>
              <TrendingUp className="h-4 w-4 text-muted-foreground mt-1" />
            </div>
            <p className="text-xs text-muted-foreground mt-3">Coordination effectiveness score</p>
          </Card>

          <Card className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Coordination Efficiency</p>
                <p className="text-2xl font-semibold tracking-tight">{effPct}%</p>
              </div>
              <CheckCircle className="h-4 w-4 text-muted-foreground mt-1" />
            </div>
            <p className="text-xs text-muted-foreground mt-3">Actual vs required coordination</p>
          </Card>
        </div>

        {/* Coordination Breakdown */}
        <Card className="p-5">
          <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground mb-4">
            Coordination Breakdown
          </p>
          <MetricRow
            label="Requirements"
            value={r.coordination_requirements_total.toLocaleString()}
            sub="Coordination pairs needed based on technical dependencies"
          />
          <MetricRow
            label="Actual Coordination"
            value={r.coordination_actuals_total.toLocaleString()}
            sub="Coordination actually happening"
          />
          <MetricRow
            label="Missed"
            value={r.missed_coordination_count.toLocaleString()}
            sub="Coordination opportunities that were missed"
            icon={<AlertTriangle className="h-3.5 w-3.5 text-red-500" />}
          />
          <MetricRow
            label="Unnecessary"
            value={r.unnecessary_coordination_count.toLocaleString()}
            sub="Coordination happening without technical need"
            icon={<XCircle className="h-3.5 w-3.5 text-orange-500" />}
          />
        </Card>

        {/* Risk indicator */}
        <div className="border border-border rounded p-4 text-sm space-y-1.5">
          <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground mb-2">
            Key Insights
          </p>
          {(1 - r.stc_value) < 0.3 && (
            <p className="flex items-start gap-2">
              <span className="text-red-500 mt-0.5">•</span>
              <span className="text-sm text-muted-foreground">
                Low STC score ({((1 - r.stc_value) * 100).toFixed(1)}%) indicates significant coordination gaps.
              </span>
            </p>
          )}
          {r.missed_coordination_count > 100 && (
            <p className="flex items-start gap-2">
              <span className="text-orange-500 mt-0.5">•</span>
              <span className="text-sm text-muted-foreground">
                High missed coordination count. Review team communication practices.
              </span>
            </p>
          )}
          {r.coordination_efficiency > 0.7 && (
            <p className="flex items-start gap-2">
              <span className="text-green-500 mt-0.5">•</span>
              <span className="text-sm text-muted-foreground">
                Good coordination efficiency — team is effectively coordinating where needed.
              </span>
            </p>
          )}
          {r.unnecessary_coordination_count > 50 && (
            <p className="flex items-start gap-2">
              <span className="text-muted-foreground mt-0.5">•</span>
              <span className="text-sm text-muted-foreground">
                Some unnecessary coordination detected — may indicate over-communication or unclear responsibilities.
              </span>
            </p>
          )}
          {(1 - r.stc_value) >= 0.3 && r.missed_coordination_count <= 100 && r.unnecessary_coordination_count <= 50 && (
            <p className="text-sm text-muted-foreground">No significant issues detected.</p>
          )}
        </div>
      </div>
    );
  }

  // ─── MC-STC content ──────────────────────────────────────────────────────────

  function renderMCSTCContent() {
    if (!mcstcResult) return null;

    return (
      <div className="space-y-6 pt-2">
        {/* Overview metrics */}
        <div className="grid grid-cols-3 gap-4">
          <Card className="p-5">
            <p className="text-xs text-muted-foreground mb-1">MC-STC Value</p>
            <p className={`text-2xl font-semibold tracking-tight ${(1 - mcstcResult.mcstc_value) > 0.7 ? "text-green-600" : (1 - mcstcResult.mcstc_value) > 0.3 ? "text-orange-600" : "text-red-600"}`}>
              {((1 - mcstcResult.mcstc_value) * 100).toFixed(1)}%
            </p>
          </Card>
          <Card className="p-5">
            <p className="text-xs text-muted-foreground mb-1">Inter-Class Score</p>
            <p className="text-2xl font-semibold tracking-tight">
              {mcstcResult.inter_class_coordination_score?.toFixed(2) ?? "—"}
            </p>
          </Card>
          <Card className="p-5">
            <p className="text-xs text-muted-foreground mb-1">Intra-Class Score</p>
            <p className="text-2xl font-semibold tracking-tight">
              {mcstcResult.intra_class_coordination_score?.toFixed(2) ?? "—"}
            </p>
          </Card>
        </div>

        {/* Role Coordination Matrix */}
        {mcstcResult.role_coordination_matrix && (
          <Card className="p-5">
            <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground mb-4">
              Role Coordination Matrix
            </p>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr>
                    <th className="border border-border p-2 text-left text-xs text-muted-foreground bg-muted/30">
                      From \ To
                    </th>
                    {Object.keys(mcstcResult.role_coordination_matrix).map((role) => (
                      <th
                        key={role}
                        className="border border-border p-2 text-center text-xs text-muted-foreground bg-muted/30 capitalize"
                      >
                        {role}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(mcstcResult.role_coordination_matrix).map(
                    ([fromRole, toRoles]: [string, any]) => (
                      <tr key={fromRole}>
                        <td className="border border-border p-2 font-medium capitalize text-xs bg-muted/30">
                          {fromRole}
                        </td>
                        {Object.keys(mcstcResult.role_coordination_matrix).map((toRole) => {
                          const value = toRoles[toRole] || 0;
                          const intensity = Math.min(value / 10, 1);
                          const textColor =
                            intensity > 0.7
                              ? "text-red-600"
                              : intensity > 0.4
                              ? "text-orange-600"
                              : intensity > 0
                              ? "text-green-600"
                              : "text-muted-foreground";
                          return (
                            <td
                              key={toRole}
                              className="border border-border p-2 text-center"
                            >
                              <span className={`text-sm font-semibold ${textColor}`}>
                                {value.toFixed(2)}
                              </span>
                            </td>
                          );
                        })}
                      </tr>
                    )
                  )}
                </tbody>
              </table>
              <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
                <span className="text-green-600">● Low (0–0.4)</span>
                <span className="text-orange-600">● Medium (0.4–0.7)</span>
                <span className="text-red-600">● High (&gt;0.7)</span>
              </div>
            </div>
          </Card>
        )}

        {/* Coordination Pairs filters */}
        <div className="flex items-center gap-4 py-2 border-y border-border">
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground">Show</label>
            <Select
              value={topN.toString()}
              onValueChange={(v) => {
                setTopN(parseInt(v));
                if (mcstcId) fetchMCSTCData();
              }}
            >
              <SelectTrigger className="w-[90px] h-7 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="5">Top 5</SelectItem>
                <SelectItem value="10">Top 10</SelectItem>
                <SelectItem value="20">Top 20</SelectItem>
                <SelectItem value="50">Top 50</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground">Status</label>
            <Select
              value={statusFilter}
              onValueChange={(v) => {
                setStatusFilter(v);
                if (mcstcId) fetchMCSTCData();
              }}
            >
              <SelectTrigger className="w-[130px] h-7 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="missed">Missed</SelectItem>
                <SelectItem value="adequate">Adequate</SelectItem>
                <SelectItem value="unnecessary">Unnecessary</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button onClick={fetchMCSTCData} variant="ghost" size="sm" className="ml-auto">
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Refresh
          </Button>
        </div>

        {/* Coordination Pairs */}
        <div className="space-y-2">
          <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground">
            Top Coordination Pairs
          </p>
          {pairs.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No coordination pairs found for the selected filters.
            </p>
          ) : (
            <div className="space-y-3">
              {pairs.map((pair, index) => (
                <Card key={pair.id} className="p-4">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-muted-foreground w-5">
                        #{index + 1}
                      </span>
                      <StatusBadge pair={pair} />
                      {pair.is_inter_class && (
                        <span className="text-xs border rounded px-1.5 py-0.5 bg-transparent border-border text-muted-foreground">
                          Inter-Class
                        </span>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-muted-foreground">Impact</p>
                      <p className="text-base font-semibold tracking-tight">
                        {pair.impact_score.toFixed(1)}
                      </p>
                    </div>
                  </div>

                  {/* Contributors */}
                  <div className="flex items-center gap-3 mb-3">
                    <div className="flex-1 border border-border rounded p-2.5">
                      <RoleTag role={pair.contributor1_role} />
                      <p className="text-xs font-medium mt-1.5 truncate" title={pair.contributor1_email}>
                        {pair.contributor1_email}
                      </p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
                    <div className="flex-1 border border-border rounded p-2.5">
                      <RoleTag role={pair.contributor2_role} />
                      <p className="text-xs font-medium mt-1.5 truncate" title={pair.contributor2_email}>
                        {pair.contributor2_email}
                      </p>
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="border border-border rounded p-2">
                      <p className="text-xs text-muted-foreground mb-0.5">Required</p>
                      <p className="text-sm font-semibold">
                        {pair.coordination_requirement > 1
                          ? pair.coordination_requirement.toFixed(0)
                          : (pair.coordination_requirement * 100).toFixed(1) + "%"}
                      </p>
                    </div>
                    <div className="border border-border rounded p-2">
                      <p className="text-xs text-muted-foreground mb-0.5">Actual</p>
                      <p className="text-sm font-semibold">
                        {pair.actual_coordination > 1
                          ? pair.actual_coordination.toFixed(0)
                          : (pair.actual_coordination * 100).toFixed(1) + "%"}
                      </p>
                    </div>
                    <div className="border border-border rounded p-2">
                      <p className="text-xs text-muted-foreground mb-0.5">Gap</p>
                      <p
                        className={`text-sm font-semibold ${
                          pair.coordination_gap > 0.1
                            ? "text-red-600"
                            : pair.coordination_gap < -0.1
                            ? "text-orange-600"
                            : "text-foreground"
                        }`}
                      >
                        {pair.coordination_gap > 0 ? "+" : ""}
                        {Math.abs(pair.coordination_gap) > 1
                          ? pair.coordination_gap.toFixed(0)
                          : (pair.coordination_gap * 100).toFixed(1) + "%"}
                      </p>
                    </div>
                  </div>

                  {/* Shared files */}
                  {pair.shared_files && pair.shared_files.length > 0 && (
                    <div className="pt-3 mt-3 border-t border-border">
                      <div className="flex items-center gap-1.5 mb-1.5">
                        <FileCode className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">
                          Shared Files ({pair.shared_files.length})
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {pair.shared_files.slice(0, 5).map((file, idx) => (
                          <span
                            key={idx}
                            className="text-xs border border-border rounded px-1.5 py-0.5 text-muted-foreground"
                          >
                            {file.split("/").pop()}
                          </span>
                        ))}
                        {pair.shared_files.length > 5 && (
                          <span className="text-xs border border-border rounded px-1.5 py-0.5 text-muted-foreground">
                            +{pair.shared_files.length - 5} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }
}
