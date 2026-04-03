"use client";

import { useEffect, useState } from "react";
import Card from "@/components/horizon/Card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { GitBranch, Calendar, Eye, RefreshCw, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api/client";
import type { ApiResponse } from "@/lib/types/response";

interface AnalysisRecord {
  id: string;
  analysis_date: string;
  branch_analyzed: string;
  stc_value: number;
  is_completed: boolean;
  mcstc_value?: number;
  created_at: string;
}

interface GroupedAnalysis {
  branch: string;
  stc: AnalysisRecord | null;
  mcstc: AnalysisRecord | null;
  latestDate: number;
}

interface AnalyticsHistoryProps {
  projectId: string;
  onViewDetails: (record: { stcId?: string; mcstcId?: string; branch: string }) => void;
}

function getScoreLevel(score: number | null): "high" | "medium" | "low" | null {
  if (score === null) return null;
  return score > 70 ? "high" : score > 30 ? "medium" : "low";
}

function ScoreDisplay({ score }: { score: number | null }) {
  const level = getScoreLevel(score);
  if (score === null || level === null) return <span className="text-sm text-muted-foreground">—</span>;

  const colorClass =
    level === "high"
      ? "text-green-600 border-green-300"
      : level === "medium"
      ? "text-orange-600 border-orange-300"
      : "text-red-600 border-red-300";

  const label = level === "high" ? "Good" : level === "medium" ? "Fair" : "Poor";

  return (
    <div className="inline-flex flex-col items-center gap-1">
      <span className={`text-sm font-semibold tracking-tight ${colorClass.split(" ")[0]}`}>
        {score.toFixed(1)}%
      </span>
      <span className={`text-xs border rounded px-1.5 py-0.5 bg-transparent ${colorClass}`}>
        {label}
      </span>
    </div>
  );
}

export function AnalyticsHistory({ projectId, onViewDetails }: AnalyticsHistoryProps) {
  const [analyses, setAnalyses] = useState<GroupedAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [branchFilter, setBranchFilter] = useState<string>("all");

  useEffect(() => {
    fetchAnalyses();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const fetchAnalyses = async () => {
    setLoading(true);
    setError(null);
    try {
      const [stcResponse, mcstcResponse] = await Promise.all([
        apiClient.get<ApiResponse<any>>(`/stc/analyses/?project_id=${projectId}`),
        apiClient.get<ApiResponse<any>>(`/mcstc/analyses/?project_id=${projectId}`),
      ]);

      const stcAnalyses = stcResponse.data.data?.results || [];
      const mcstcAnalyses = mcstcResponse.data.data?.results || [];

      const branchMap = new Map<string, any>();

      stcAnalyses.forEach((stc: any) => {
        const branch = stc.branch_analyzed || "";
        if (!branchMap.has(branch)) branchMap.set(branch, { branch, stc: null, mcstc: null });
        const existing = branchMap.get(branch);
        if (!existing.stc || new Date(stc.analysis_date) > new Date(existing.stc.analysis_date)) {
          existing.stc = stc;
        }
      });

      mcstcAnalyses.forEach((mcstc: any) => {
        const branch = mcstc.branch_analyzed || "";
        if (!branchMap.has(branch)) branchMap.set(branch, { branch, stc: null, mcstc: null });
        const existing = branchMap.get(branch);
        if (!existing.mcstc || new Date(mcstc.analysis_date) > new Date(existing.mcstc.analysis_date)) {
          existing.mcstc = mcstc;
        }
      });

      const combined = Array.from(branchMap.values())
        .map((item) => ({
          ...item,
          latestDate: Math.max(
            item.stc ? new Date(item.stc.analysis_date).getTime() : 0,
            item.mcstc ? new Date(item.mcstc.analysis_date).getTime() : 0
          ),
        }))
        .sort((a, b) => b.latestDate - a.latestDate);

      setAnalyses(combined);
    } catch (err: any) {
      console.error("Failed to load analyses:", err);
      setError("Failed to load analysis history");
    } finally {
      setLoading(false);
    }
  };

  const branches = Array.from(
    new Set(analyses.map((a) => a.branch).filter((b) => b && b.trim() !== ""))
  );

  const filteredAnalyses = analyses.filter(
    (a) => branchFilter === "all" || a.branch === branchFilter
  );

  if (loading) {
    return (
      <Card className="p-8">
        <div className="flex items-center justify-center gap-2 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-xs">Loading analysis history...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-8">
        <p className="text-center text-sm text-destructive">{error}</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground mb-0.5">
            Analysis History
          </p>
          <p className="text-sm text-muted-foreground">
            {filteredAnalyses.length} record{filteredAnalyses.length !== 1 ? "s" : ""} found
          </p>
        </div>
        <Button onClick={fetchAnalyses} variant="ghost" size="sm">
          <RefreshCw className="h-3.5 w-3.5 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Branch filter */}
      {branches.length > 1 && (
        <div className="flex items-center gap-2">
          <Select value={branchFilter} onValueChange={setBranchFilter}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="All Branches" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Branches</SelectItem>
              {branches.map((branch, i) => (
                <SelectItem key={`${branch}-${i}`} value={branch}>
                  {branch}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Table */}
      <Card>
        {filteredAnalyses.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">
            No analysis records found. Run STC or MC-STC analysis to see history.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-4 py-3 text-xs font-medium tracking-widest uppercase text-muted-foreground">
                    Branch
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium tracking-widest uppercase text-muted-foreground">
                    Date
                  </th>
                  <th className="text-center px-4 py-3 text-xs font-medium tracking-widest uppercase text-muted-foreground">
                    STC Score
                  </th>
                  <th className="text-center px-4 py-3 text-xs font-medium tracking-widest uppercase text-muted-foreground">
                    MC-STC Score
                  </th>
                  <th className="text-center px-4 py-3 text-xs font-medium tracking-widest uppercase text-muted-foreground">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredAnalyses.map((record, index) => {
                  const stcScore = record.stc?.stc_value;
                  const mcstcScore = record.mcstc?.mcstc_value;
                  const stcScorePct =
                    record.stc?.is_completed && stcScore != null
                      ? (1 - stcScore) * 100
                      : null;
                  const mcstcScorePct =
                    record.mcstc?.is_completed && mcstcScore != null
                      ? (1 - mcstcScore) * 100
                      : null;

                  const dateStr = (record.stc ?? record.mcstc)?.analysis_date;

                  return (
                    <tr
                      key={`${record.branch}-${index}`}
                      className="border-b border-border hover:bg-muted/40 transition-colors"
                    >
                      {/* Branch */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <GitBranch className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                          <span className="text-sm font-medium">{record.branch || "(default)"}</span>
                        </div>
                      </td>

                      {/* Date */}
                      <td className="px-4 py-3">
                        {dateStr ? (
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Calendar className="h-3.5 w-3.5 shrink-0" />
                            <span className="text-xs">
                              {new Date(dateStr).toLocaleDateString("en-US", {
                                month: "short",
                                day: "numeric",
                                year: "numeric",
                              })}
                            </span>
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </td>

                      {/* STC Score */}
                      <td className="px-4 py-3 text-center">
                        {record.stc && !record.stc.is_completed ? (
                          <span className="text-xs text-muted-foreground">In progress</span>
                        ) : (
                          <ScoreDisplay score={stcScorePct} />
                        )}
                      </td>

                      {/* MC-STC Score */}
                      <td className="px-4 py-3 text-center">
                        {record.mcstc && !record.mcstc.is_completed ? (
                          <span className="text-xs text-muted-foreground">In progress</span>
                        ) : (
                          <ScoreDisplay score={mcstcScorePct} />
                        )}
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3 text-center">
                        {(record.stc?.is_completed || record.mcstc?.is_completed) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              onViewDetails({
                                stcId: record.stc?.is_completed ? record.stc.id : undefined,
                                mcstcId: record.mcstc?.is_completed ? record.mcstc.id : undefined,
                                branch: record.branch,
                              })
                            }
                          >
                            <Eye className="h-3.5 w-3.5 mr-1.5" />
                            Details
                          </Button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
