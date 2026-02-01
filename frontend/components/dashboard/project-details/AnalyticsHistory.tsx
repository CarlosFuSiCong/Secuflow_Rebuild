"use client";

import { useEffect, useState } from "react";
import Card from "@/components/horizon/Card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { GitBranch, Calendar, TrendingUp, TrendingDown, Eye, RefreshCw, Activity, BarChart3 } from "lucide-react";
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
  latestDate: number; // timestamp for sorting
}

interface AnalyticsHistoryProps {
  projectId: string;
  onViewDetails: (record: { stcId?: string; mcstcId?: string; branch: string }) => void;
}

export function AnalyticsHistory({ projectId, onViewDetails }: AnalyticsHistoryProps) {
  const [analyses, setAnalyses] = useState<GroupedAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [branchFilter, setBranchFilter] = useState<string>("all");

  useEffect(() => {
    fetchAnalyses();
  }, [projectId]);

  const fetchAnalyses = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch STC analyses
      const stcResponse = await apiClient.get<ApiResponse<any>>(
        `/stc/analyses/?project_id=${projectId}`
      );
      
      console.log('=== STC Response ===');
      console.log('Full Response:', stcResponse);
      console.log('Response Data:', stcResponse.data);
      
      // Fetch MC-STC analyses
      const mcstcResponse = await apiClient.get<ApiResponse<any>>(
        `/mcstc/analyses/?project_id=${projectId}`
      );
      
      console.log('=== MC-STC Response ===');
      console.log('Full Response:', mcstcResponse);
      console.log('Response Data:', mcstcResponse.data);
      console.log('Response Data.data:', mcstcResponse.data.data);
      console.log('Response Data.data?.results:', mcstcResponse.data.data?.results);
      
      const stcAnalyses = stcResponse.data.data?.results || [];
      const mcstcAnalyses = mcstcResponse.data.data?.results || mcstcResponse.data.results || [];
      
      console.log('=== Analysis History Data ===');
      console.log('STC Analyses Count:', stcAnalyses.length);
      console.log('STC Analyses:', stcAnalyses);
      console.log('MC-STC Analyses Count:', mcstcAnalyses.length);
      console.log('MC-STC Analyses:', mcstcAnalyses);
      
      // Group by branch - show latest STC and MC-STC for each branch
      const branchMap = new Map<string, any>();
      
      // Group STC analyses by branch (keep latest for each branch)
      stcAnalyses.forEach((stc: any) => {
        const branch = stc.branch_analyzed || '';
        if (!branchMap.has(branch)) {
          branchMap.set(branch, { branch, stc: null, mcstc: null });
        }
        const existing = branchMap.get(branch);
        // Keep the latest STC
        if (!existing.stc || new Date(stc.analysis_date) > new Date(existing.stc.analysis_date)) {
          existing.stc = stc;
        }
      });
      
      // Group MC-STC analyses by branch (keep latest for each branch)
      mcstcAnalyses.forEach((mcstc: any) => {
        const branch = mcstc.branch_analyzed || '';
        console.log('Processing MC-STC for branch:', branch, mcstc);
        if (!branchMap.has(branch)) {
          branchMap.set(branch, { branch, stc: null, mcstc: null });
        }
        const existing = branchMap.get(branch);
        // Keep the latest MC-STC
        if (!existing.mcstc || new Date(mcstc.analysis_date) > new Date(existing.mcstc.analysis_date)) {
          existing.mcstc = mcstc;
          console.log('Updated MC-STC for branch:', branch, existing);
        }
      });
      
      // Convert to array and sort by latest analysis date
      const combined = Array.from(branchMap.values())
        .map(item => ({
          ...item,
          // Use the latest date between STC and MC-STC
          latestDate: Math.max(
            item.stc ? new Date(item.stc.analysis_date).getTime() : 0,
            item.mcstc ? new Date(item.mcstc.analysis_date).getTime() : 0
          )
        }))
        .sort((a, b) => b.latestDate - a.latestDate);
      
      console.log('Branch Map:', branchMap);
      console.log('Combined Results:', combined);
      console.log('Total Branches:', combined.length);
      
      setAnalyses(combined);
    } catch (err: any) {
      console.error("Failed to load analyses:", err);
      setError("Failed to load analysis history");
    } finally {
      setLoading(false);
    }
  };

  // Get unique branches (filter out empty strings)
  const branches = Array.from(new Set(analyses.map(a => a.branch).filter(b => b && b.trim() !== '')));

  // Filter analyses
  const filteredAnalyses = analyses.filter(analysis => {
    if (branchFilter !== "all" && analysis.branch !== branchFilter) {
      return false;
    }
    return true;
  });

  if (loading) {
    return (
      <Card className="p-8">
        <div className="flex items-center justify-center">
          <RefreshCw className="h-6 w-6 animate-spin text-primary" />
          <span className="ml-2">Loading analysis history...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-8">
        <div className="text-center text-destructive">{error}</div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header and Filters */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Analysis History</h3>
          <p className="text-sm text-muted-foreground">
            All STC and MC-STC analyses for this project ({filteredAnalyses.length} records)
          </p>
        </div>
        <Button onClick={fetchAnalyses} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        <Select value={branchFilter} onValueChange={setBranchFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All Branches" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Branches</SelectItem>
            {branches.map((branch, index) => (
              <SelectItem key={`branch-${branch}-${index}`} value={branch}>
                {branch}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Analysis Table */}
      <Card>
        {filteredAnalyses.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No analysis records found. Run STC or MC-STC analysis to see history.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b bg-muted/50">
                <tr>
                  <th className="text-left p-4 font-medium">Branch</th>
                  <th className="text-left p-4 font-medium">Analysis Date</th>
                  <th className="text-center p-4 font-medium">STC Score</th>
                  <th className="text-center p-4 font-medium">MC-STC Score</th>
                  <th className="text-center p-4 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filteredAnalyses.map((record, index) => {
                  const stcScore = record.stc?.stc_value;
                  const mcstcScore = record.mcstc?.mcstc_value;
                  const stcRisk = stcScore !== null && stcScore !== undefined ? (1.0 - stcScore) * 100 : null;
                  const mcstcRisk = mcstcScore !== null && mcstcScore !== undefined ? (1.0 - mcstcScore) * 100 : null;
                  
                  const getRiskLevel = (risk: number | null) => {
                    if (risk === null) return null;
                    return risk < 30 ? "low" : risk < 60 ? "medium" : "high";
                  };
                  
                  const stcRiskLevel = getRiskLevel(stcRisk);
                  const mcstcRiskLevel = getRiskLevel(mcstcRisk);
                  
                  return (
                    <tr key={`analysis-${record.branch}-${index}`} className="hover:bg-muted/30">
                      {/* Branch */}
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <GitBranch className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{record.branch || "(empty)"}</span>
                        </div>
                      </td>
                      
                      {/* Analysis Date (from STC) */}
                      <td className="p-4">
                        {record.stc ? (
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm">
                              {new Date(record.stc.analysis_date).toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </span>
                          </div>
                        ) : record.mcstc ? (
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm">
                              {new Date(record.mcstc.analysis_date).toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </span>
                          </div>
                        ) : (
                          <span className="text-sm text-muted-foreground">—</span>
                        )}
                      </td>
                      
                      {/* STC Score */}
                      <td className="p-4 text-center">
                        {record.stc?.is_completed && stcRisk !== null ? (
                          <div className="inline-flex flex-col items-center gap-1">
                            <span className={`text-lg font-bold ${
                              stcRiskLevel === "low" ? "text-green-600" : 
                              stcRiskLevel === "medium" ? "text-yellow-600" : 
                              "text-red-600"
                            }`}>
                              {stcRisk.toFixed(1)}%
                            </span>
                            <Badge variant="outline" className={`text-xs ${
                              stcRiskLevel === "low" ? "border-green-500 text-green-700" : 
                              stcRiskLevel === "medium" ? "border-yellow-500 text-yellow-700" : 
                              "border-red-500 text-red-700"
                            }`}>
                              {stcRiskLevel === "low" ? "Low" : stcRiskLevel === "medium" ? "Medium" : "High"}
                            </Badge>
                          </div>
                        ) : record.stc ? (
                          <span className="text-sm text-muted-foreground">In Progress...</span>
                        ) : (
                          <span className="text-sm text-muted-foreground">N/A</span>
                        )}
                      </td>
                      
                      {/* MC-STC Score */}
                      <td className="p-4 text-center">
                        {record.mcstc?.is_completed && mcstcRisk !== null ? (
                          <div className="inline-flex flex-col items-center gap-1">
                            <span className={`text-lg font-bold ${
                              mcstcRiskLevel === "low" ? "text-green-600" : 
                              mcstcRiskLevel === "medium" ? "text-yellow-600" : 
                              "text-red-600"
                            }`}>
                              {mcstcRisk.toFixed(1)}%
                            </span>
                            <Badge variant="outline" className={`text-xs ${
                              mcstcRiskLevel === "low" ? "border-green-500 text-green-700" : 
                              mcstcRiskLevel === "medium" ? "border-yellow-500 text-yellow-700" : 
                              "border-red-500 text-red-700"
                            }`}>
                              {mcstcRiskLevel === "low" ? "Low" : mcstcRiskLevel === "medium" ? "Medium" : "High"}
                            </Badge>
                          </div>
                        ) : record.mcstc ? (
                          <span className="text-sm text-muted-foreground">In Progress...</span>
                        ) : (
                          <span className="text-sm text-muted-foreground">N/A</span>
                        )}
                      </td>
                      
                      {/* Actions */}
                      <td className="p-4 text-center">
                        {(record.stc?.is_completed || record.mcstc?.is_completed) && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onViewDetails({
                              stcId: record.stc?.is_completed ? record.stc.id : undefined,
                              mcstcId: record.mcstc?.is_completed ? record.mcstc.id : undefined,
                              branch: record.branch
                            })}
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            View Details
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
