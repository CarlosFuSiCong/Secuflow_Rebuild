"use client";

import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
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
  TrendingDown, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  FileCode,
  ArrowRight,
  BarChart3,
  AlertCircle
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

export function CoordinationPairsModal({ 
  stcId,
  mcstcId,
  branch,
  open, 
  onClose 
}: CoordinationPairsModalProps) {
  const [activeTab, setActiveTab] = useState<'stc' | 'mcstc'>('stc');
  const [pairs, setPairs] = useState<CoordinationPair[]>([]);
  const [stcResult, setStcResult] = useState<STCResult | null>(null);
  const [mcstcResult, setMcstcResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [topN, setTopN] = useState<number>(10);

  // Auto-select tab based on available data
  useEffect(() => {
    if (open) {
      if (mcstcId && !stcId) {
        setActiveTab('mcstc');
      } else {
        setActiveTab('stc');
      }
    }
  }, [open, stcId, mcstcId]);

  useEffect(() => {
    if (open) {
      if (activeTab === 'stc' && stcId) {
        fetchSTCResult();
      } else if (activeTab === 'mcstc' && mcstcId) {
        fetchMCSTCData();
      }
    }
  }, [open, activeTab, stcId, mcstcId, statusFilter, topN]);

  const fetchSTCResult = async () => {
    if (!stcId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await stcApi.getSTCResults(stcId);
      setStcResult(result);
    } catch (err: any) {
      console.error("Failed to load STC results:", err);
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
      // Fetch coordination pairs
      const pairsResult = await mcstcApi.getCoordinationPairs(mcstcId, {
        topN,
        statusFilter: statusFilter === 'all' ? undefined : statusFilter as any
      });
      setPairs(pairsResult.coordination_pairs);

      // Fetch full MC-STC results
      const mcstcResults = await mcstcApi.getMCSTCResults(mcstcId);
      setMcstcResult(mcstcResults);
    } catch (err: any) {
      console.error("Failed to load MC-STC data:", err);
      console.error("Error details:", {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status
      });
      setError("Failed to load MC-STC data: " + (err.response?.data?.message || err.message));
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (pair: CoordinationPair) => {
    if (pair.is_missed_coordination) {
      return (
        <Badge variant="outline" className="border-red-500 text-red-700 bg-red-50 dark:bg-red-950/20">
          <AlertTriangle className="h-3 w-3 mr-1" />
          Missed
        </Badge>
      );
    } else if (pair.is_unnecessary_coordination) {
      return (
        <Badge variant="outline" className="border-yellow-500 text-yellow-700 bg-yellow-50 dark:bg-yellow-950/20">
          <XCircle className="h-3 w-3 mr-1" />
          Unnecessary
        </Badge>
      );
    } else {
      return (
        <Badge variant="outline" className="border-green-500 text-green-700 bg-green-50 dark:bg-green-950/20">
          <CheckCircle className="h-3 w-3 mr-1" />
          Adequate
        </Badge>
      );
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role.toLowerCase()) {
      case 'developer':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300';
      case 'security':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300';
      case 'ops':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-7xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Analysis Details - {branch}
          </DialogTitle>
        </DialogHeader>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 border-b pb-2">
          {stcId && (
            <Button
              variant={activeTab === 'stc' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('stc')}
            >
              STC Analysis
            </Button>
          )}
          {mcstcId && (
            <Button
              variant={activeTab === 'mcstc' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('mcstc')}
            >
              MC-STC Analysis
            </Button>
          )}
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-6 w-6 animate-spin text-primary" />
            <span className="ml-2">Loading analysis data...</span>
          </div>
        ) : error ? (
          <div className="text-center py-12 text-destructive">{error}</div>
        ) : (
          <>
            {activeTab === 'stc' && stcResult && renderSTCContent()}
            {activeTab === 'mcstc' && mcstcResult && renderMCSTCContent()}
          </>
        )}
      </DialogContent>
    </Dialog>
  );

  function renderSTCContent() {
    if (!stcResult) return null;
    return (
            <div className="space-y-6">
              {/* Overview Card */}
              <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20">
                <h3 className="text-lg font-semibold mb-4">Analysis Overview</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-muted-foreground">Branch</div>
                    <div className="text-lg font-medium">{stcResult.results.branch_analyzed || 'N/A'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Analysis Date</div>
                    <div className="text-lg font-medium">
                      {new Date(stcResult.analysis_date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Contributors</div>
                    <div className="text-lg font-medium">{stcResult.results.contributors_count}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Files Analyzed</div>
                    <div className="text-lg font-medium">{stcResult.results.files_count}</div>
                  </div>
                </div>
              </Card>

              {/* Main Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* STC Value */}
                <Card className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="text-sm text-muted-foreground mb-1">STC Value</div>
                      <div className="text-4xl font-bold text-blue-600 dark:text-blue-400">
                        {(stcResult.results.stc_value * 100).toFixed(1)}%
                      </div>
                    </div>
                    <TrendingUp className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Coordination effectiveness score
                  </div>
                </Card>

                {/* Coordination Efficiency */}
                <Card className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="text-sm text-muted-foreground mb-1">Coordination Efficiency</div>
                      <div className="text-4xl font-bold text-green-600 dark:text-green-400">
                        {(stcResult.results.coordination_efficiency * 100).toFixed(1)}%
                      </div>
                    </div>
                    <CheckCircle className="h-8 w-8 text-green-600 dark:text-green-400" />
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Actual vs required coordination
                  </div>
                </Card>
              </div>

              {/* Coordination Details */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Coordination Breakdown</h3>
                <div className="space-y-4">
                  {/* Requirements */}
                  <div className="flex items-center justify-between p-4 rounded-lg bg-blue-50 dark:bg-blue-950/20">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                      <div>
                        <div className="font-medium">Coordination Requirements</div>
                        <div className="text-xs text-muted-foreground">
                          Total coordination pairs needed based on technical dependencies
                        </div>
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {stcResult.results.coordination_requirements_total.toLocaleString()}
                    </div>
                  </div>

                  {/* Actuals */}
                  <div className="flex items-center justify-between p-4 rounded-lg bg-green-50 dark:bg-green-950/20">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-green-500"></div>
                      <div>
                        <div className="font-medium">Actual Coordination</div>
                        <div className="text-xs text-muted-foreground">
                          Coordination actually happening (from communication data)
                        </div>
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {stcResult.results.coordination_actuals_total.toLocaleString()}
                    </div>
                  </div>

                  {/* Missed */}
                  <div className="flex items-center justify-between p-4 rounded-lg bg-red-50 dark:bg-red-950/20">
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="h-5 w-5 text-red-500" />
                      <div>
                        <div className="font-medium">Missed Coordination</div>
                        <div className="text-xs text-muted-foreground">
                          Coordination opportunities that were missed
                        </div>
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                      {stcResult.results.missed_coordination_count.toLocaleString()}
                    </div>
                  </div>

                  {/* Unnecessary */}
                  <div className="flex items-center justify-between p-4 rounded-lg bg-yellow-50 dark:bg-yellow-950/20">
                    <div className="flex items-center gap-3">
                      <XCircle className="h-5 w-5 text-yellow-500" />
                      <div>
                        <div className="font-medium">Unnecessary Coordination</div>
                        <div className="text-xs text-muted-foreground">
                          Coordination happening without technical need
                        </div>
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                      {stcResult.results.unnecessary_coordination_count.toLocaleString()}
                    </div>
                  </div>
                </div>
              </Card>

              {/* Insights */}
              <Card className="p-6 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950/20 dark:to-pink-950/20">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <AlertCircle className="h-5 w-5" />
                  Key Insights
                </h3>
                <div className="space-y-2 text-sm">
                  {stcResult.results.stc_value < 0.3 && (
                    <div className="flex items-start gap-2">
                      <span className="text-red-500">•</span>
                      <span>Low STC value indicates significant coordination gaps. Consider improving communication channels.</span>
                    </div>
                  )}
                  {stcResult.results.missed_coordination_count > 100 && (
                    <div className="flex items-start gap-2">
                      <span className="text-yellow-500">•</span>
                      <span>High number of missed coordination opportunities detected. Review team communication practices.</span>
                    </div>
                  )}
                  {stcResult.results.coordination_efficiency > 0.7 && (
                    <div className="flex items-start gap-2">
                      <span className="text-green-500">•</span>
                      <span>Good coordination efficiency! Team is effectively coordinating where needed.</span>
                    </div>
                  )}
                  {stcResult.results.unnecessary_coordination_count > 50 && (
                    <div className="flex items-start gap-2">
                      <span className="text-blue-500">•</span>
                      <span>Some unnecessary coordination detected. May indicate over-communication or unclear responsibilities.</span>
                    </div>
                  )}
                </div>
              </Card>
            </div>
    );
  }

  function renderMCSTCContent() {
    if (!mcstcResult) return null;

    return (
      <div className="space-y-6">
        {/* MC-STC Overview */}
        <Card className="p-6 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950/20 dark:to-pink-950/20">
          <h3 className="text-lg font-semibold mb-4">MC-STC Analysis Overview</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                {(mcstcResult.mcstc_value * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-muted-foreground mt-1">MC-STC Value</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {mcstcResult.inter_class_coordination_score?.toFixed(2) || 'N/A'}
              </div>
              <div className="text-sm text-muted-foreground mt-1">Inter-Class Score</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                {mcstcResult.intra_class_coordination_score?.toFixed(2) || 'N/A'}
              </div>
              <div className="text-sm text-muted-foreground mt-1">Intra-Class Score</div>
            </div>
          </div>
        </Card>

        {/* Role Coordination Matrix Visualization */}
        {mcstcResult.role_coordination_matrix && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Users className="h-5 w-5" />
              Role Coordination Matrix
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className="border p-2 bg-muted text-left">From \ To</th>
                    {Object.keys(mcstcResult.role_coordination_matrix).map((role) => (
                      <th key={role} className="border p-2 bg-muted text-center capitalize">
                        {role}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(mcstcResult.role_coordination_matrix).map(([fromRole, toRoles]: [string, any]) => (
                    <tr key={fromRole}>
                      <td className="border p-2 font-medium capitalize bg-muted">{fromRole}</td>
                      {Object.entries(mcstcResult.role_coordination_matrix).map(([toRole]) => {
                        const value = toRoles[toRole] || 0;
                        const intensity = Math.min(value / 10, 1); // Normalize to 0-1
                        const bgColor = 
                          intensity > 0.7 ? 'bg-red-100 dark:bg-red-950/30' :
                          intensity > 0.4 ? 'bg-yellow-100 dark:bg-yellow-950/30' :
                          intensity > 0 ? 'bg-green-100 dark:bg-green-950/30' :
                          'bg-gray-50 dark:bg-gray-900/30';
                        
                        return (
                          <td key={toRole} className={`border p-2 text-center ${bgColor}`}>
                            <div className="font-semibold">{value.toFixed(2)}</div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="mt-2 text-xs text-muted-foreground">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1">
                    <div className="w-4 h-4 bg-green-100 dark:bg-green-950/30 border"></div>
                    Low (0-0.4)
                  </span>
                  <span className="flex items-center gap-1">
                    <div className="w-4 h-4 bg-yellow-100 dark:bg-yellow-950/30 border"></div>
                    Medium (0.4-0.7)
                  </span>
                  <span className="flex items-center gap-1">
                    <div className="w-4 h-4 bg-red-100 dark:bg-red-950/30 border"></div>
                    High (&gt;0.7)
                  </span>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Filters for Coordination Pairs */}
        <div className="flex items-center gap-4 py-2 border-y">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Show:</label>
            <Select value={topN.toString()} onValueChange={(v) => {
              setTopN(parseInt(v));
              if (mcstcId) fetchMCSTCData();
            }}>
              <SelectTrigger className="w-[100px]">
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
            <label className="text-sm font-medium">Status:</label>
            <Select value={statusFilter} onValueChange={(v) => {
              setStatusFilter(v);
              if (mcstcId) fetchMCSTCData();
            }}>
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="missed">Missed Only</SelectItem>
                <SelectItem value="adequate">Adequate Only</SelectItem>
                <SelectItem value="unnecessary">Unnecessary</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button onClick={fetchMCSTCData} variant="outline" size="sm" className="ml-auto">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Top Coordination Pairs */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Top Impact Coordination Pairs</h3>
          {pairs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No coordination pairs found for the selected filters.
            </div>
          ) : (
            <div className="space-y-4">
              {pairs.map((pair, index) => (
                <Card key={pair.id} className="p-4 hover:shadow-md transition-shadow">
                  {/* Header Row */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-bold">
                        #{index + 1}
                      </div>
                      {getStatusBadge(pair)}
                      {pair.is_inter_class && (
                        <Badge variant="outline" className="border-blue-500 text-blue-700">
                          Inter-Class
                        </Badge>
                      )}
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-muted-foreground">Impact Score</div>
                      <div className="text-2xl font-bold text-primary">
                        {pair.impact_score.toFixed(1)}
                      </div>
                    </div>
                  </div>

                  {/* Contributors */}
                  <div className="flex items-center gap-4 mb-4">
                    {/* Contributor 1 */}
                    <div className="flex-1 p-3 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge className={getRoleBadgeColor(pair.contributor1_role)}>
                          {pair.contributor1_role}
                        </Badge>
                      </div>
                      <div className="text-sm font-medium truncate" title={pair.contributor1_email}>
                        {pair.contributor1_email}
                      </div>
                      <div className="text-xs text-muted-foreground">ID: {pair.contributor1_id}</div>
                    </div>

                    {/* Arrow */}
                    <div className="flex flex-col items-center gap-1">
                      <ArrowRight className="h-6 w-6 text-muted-foreground" />
                      <div className="text-xs text-muted-foreground">coordinates with</div>
                    </div>

                    {/* Contributor 2 */}
                    <div className="flex-1 p-3 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge className={getRoleBadgeColor(pair.contributor2_role)}>
                          {pair.contributor2_role}
                        </Badge>
                      </div>
                      <div className="text-sm font-medium truncate" title={pair.contributor2_email}>
                        {pair.contributor2_email}
                      </div>
                      <div className="text-xs text-muted-foreground">ID: {pair.contributor2_id}</div>
                    </div>
                  </div>

                  {/* Metrics Grid */}
                  <div className="grid grid-cols-3 gap-4 mb-3">
                    <div className="text-center p-2 rounded bg-blue-50 dark:bg-blue-950/20">
                      <div className="text-xs text-muted-foreground mb-1">Required</div>
                      <div className="text-lg font-semibold text-blue-700 dark:text-blue-400">
                        {pair.coordination_requirement > 1 
                          ? pair.coordination_requirement.toFixed(0) 
                          : (pair.coordination_requirement * 100).toFixed(1) + '%'}
                      </div>
                    </div>
                    <div className="text-center p-2 rounded bg-green-50 dark:bg-green-950/20">
                      <div className="text-xs text-muted-foreground mb-1">Actual</div>
                      <div className="text-lg font-semibold text-green-700 dark:text-green-400">
                        {pair.actual_coordination > 1 
                          ? pair.actual_coordination.toFixed(0) 
                          : (pair.actual_coordination * 100).toFixed(1) + '%'}
                      </div>
                    </div>
                    <div className={`text-center p-2 rounded ${
                      pair.coordination_gap > 0.1 
                        ? 'bg-red-50 dark:bg-red-950/20' 
                        : pair.coordination_gap < -0.1
                        ? 'bg-yellow-50 dark:bg-yellow-950/20'
                        : 'bg-gray-50 dark:bg-gray-950/20'
                    }`}>
                      <div className="text-xs text-muted-foreground mb-1">Gap</div>
                      <div className={`text-lg font-semibold ${
                        pair.coordination_gap > 0.1 
                          ? 'text-red-700 dark:text-red-400' 
                          : pair.coordination_gap < -0.1
                          ? 'text-yellow-700 dark:text-yellow-400'
                          : 'text-gray-700 dark:text-gray-400'
                      }`}>
                        {pair.coordination_gap > 0 ? '+' : ''}
                        {Math.abs(pair.coordination_gap) > 1 
                          ? pair.coordination_gap.toFixed(0) 
                          : (pair.coordination_gap * 100).toFixed(1) + '%'}
                      </div>
                    </div>
                  </div>

                  {/* Files */}
                  {pair.shared_files && pair.shared_files.length > 0 && (
                    <div className="pt-3 border-t">
                      <div className="flex items-center gap-2 mb-2">
                        <FileCode className="h-4 w-4 text-muted-foreground" />
                        <span className="text-xs font-medium text-muted-foreground">
                          Shared Files ({pair.shared_files.length})
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {pair.shared_files.slice(0, 5).map((file, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {file.split('/').pop()}
                          </Badge>
                        ))}
                        {pair.shared_files.length > 5 && (
                          <Badge variant="outline" className="text-xs">
                            +{pair.shared_files.length - 5} more
                          </Badge>
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
