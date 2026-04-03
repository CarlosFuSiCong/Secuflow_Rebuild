import Card from "@/components/horizon/Card";
import type { ProjectHeaderProps } from "@/lib/types";
import type { Branch } from "@/lib/types/project";
import { DeleteProjectButton } from "./DeleteProjectButton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Users, GitBranch, BarChart3, AlertCircle, AlertTriangle, Loader2 } from "lucide-react";
import { useState } from "react";

interface ExtendedProjectHeaderProps extends ProjectHeaderProps {
  branches: Branch[];
  selectedBranch: string;
  onBranchChange: (branch: string) => void;
  onConfirmBranchSwitch?: (newBranch: string) => void;
  hasBasicAnalysis: boolean;
  hasFullAnalysis: boolean;
  branchesCount: number;
  isSwitchingBranch?: boolean;
}

export function ProjectHeader({ 
  project, 
  branches,
  selectedBranch,
  onBranchChange,
  onConfirmBranchSwitch,
  hasBasicAnalysis,
  hasFullAnalysis,
  branchesCount,
  isSwitchingBranch = false
}: ExtendedProjectHeaderProps) {
  const [pendingBranch, setPendingBranch] = useState<string | null>(null);

  const handleBranchSelect = (newBranch: string) => {
    if (newBranch !== selectedBranch) {
      setPendingBranch(newBranch);
    }
  };

  const handleConfirmSwitch = () => {
    if (pendingBranch && onConfirmBranchSwitch) {
      // 立即更新选中的分支（UI 立即响应）
      onBranchChange(pendingBranch);
      // 调用确认回调（后台切换）
      onConfirmBranchSwitch(pendingBranch);
      setPendingBranch(null);
    }
  };

  const handleCancelSwitch = () => {
    setPendingBranch(null);
  };

  // Check if TNM is complete for current branch
  const tnmComplete = !!project.repository_path && (project.members_count || 0) > 0;

  return (
    <Card>
      <div className="p-6">
        <div className="flex justify-between items-start mb-6">
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground mb-1">
              Project
            </p>
            <h2 className="text-xl font-semibold tracking-tight text-foreground">
              {project.name}
            </h2>
            {project.description && (
              <p className="text-sm text-muted-foreground mt-0.5">
                {project.description}
              </p>
            )}
            <p className="text-xs text-muted-foreground mt-1 truncate">
              {project.repo_url}
            </p>
          </div>
          <DeleteProjectButton projectId={project.id} projectName={project.name} />
        </div>

        {/* Branch Selector */}
        <div className="space-y-3 mb-6 pt-4 border-t border-border">
          <label className="text-xs font-medium tracking-widest uppercase text-muted-foreground">Current Branch</label>
          <div className="flex items-center gap-3">
            <Select 
              value={pendingBranch || selectedBranch} 
              onValueChange={handleBranchSelect}
            >
              <SelectTrigger className="w-full max-w-md">
                <SelectValue placeholder="Select a branch" />
              </SelectTrigger>
              <SelectContent>
                {branches.map((branch) => (
                  <SelectItem key={branch.name} value={branch.name}>
                    <div className="flex items-center gap-2">
                      <GitBranch className="h-4 w-4" />
                      {branch.name}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {pendingBranch && (
              <div className="flex gap-2">
                <Button 
                  onClick={handleConfirmSwitch}
                  size="sm"
                  variant="default"
                >
                  Confirm Switch
                </Button>
                <Button 
                  onClick={handleCancelSwitch}
                  size="sm"
                  variant="outline"
                >
                  Cancel
                </Button>
              </div>
            )}
          </div>

          {/* Warning Alert when branch change is pending */}
          {pendingBranch && (
            <Alert className="border-orange-300/60 bg-orange-50/50 dark:bg-orange-950/10 dark:border-orange-700/40">
              <AlertTriangle className="h-4 w-4 text-orange-600 dark:text-orange-400" />
              <AlertDescription className="text-orange-800 dark:text-orange-300">
                Switching to <strong>{pendingBranch}</strong> will re-clone the repository and re-run TNM and STC analysis. All existing analysis data will be replaced.
              </AlertDescription>
            </Alert>
          )}
        </div>

        {/* Statistics Grid - Show if TNM is complete or switching branch */}
        {(tnmComplete || isSwitchingBranch) && (
          <div className="border-t pt-6">
            <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground mb-4">
              Project Overview
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* Members Card */}
              <div className="flex items-center gap-3 p-4 rounded border border-border bg-card">
                <div className="p-2 rounded border border-border">
                  <Users className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-0.5">Contributors</div>
                  {isSwitchingBranch && (project.members_count || 0) === 0 ? (
                    <div className="flex items-center gap-1.5">
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">Analyzing…</span>
                    </div>
                  ) : (
                    <div className="text-lg font-semibold tracking-tight">{project.members_count || 0}</div>
                  )}
                </div>
              </div>

              {/* Branches Card */}
              <div className="flex items-center gap-3 p-4 rounded border border-border bg-card">
                <div className="p-2 rounded border border-border">
                  <GitBranch className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-0.5">Branches</div>
                  <div className="text-lg font-semibold tracking-tight">{branchesCount}</div>
                </div>
              </div>

              {/* STC Score Card */}
              <div className="flex items-center gap-3 p-4 rounded border border-border bg-card">
                <div className="p-2 rounded border border-border">
                  <BarChart3 className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-0.5">STC Score</div>
                  {isSwitchingBranch && !hasBasicAnalysis ? (
                    <div className="flex items-center gap-1.5">
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">Computing…</span>
                    </div>
                  ) : (
                    <div className="text-lg font-semibold tracking-tight">
                      {project.stc_risk_score !== null && project.stc_risk_score !== undefined
                        ? `${(project.stc_risk_score * 100).toFixed(1)}%`
                        : "N/A"}
                    </div>
                  )}
                </div>
              </div>

              {/* MC-STC Score Card */}
              <div className="flex items-center gap-3 p-4 rounded border border-border bg-card">
                <div className="p-2 rounded border border-border">
                  <AlertCircle className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-0.5">MC-STC Score</div>
                  {isSwitchingBranch && !hasFullAnalysis ? (
                    <div className="flex items-center gap-1.5">
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">Computing…</span>
                    </div>
                  ) : (
                    <div className="text-lg font-semibold tracking-tight">
                      {project.mcstc_risk_score !== null && project.mcstc_risk_score !== undefined
                        ? `${(project.mcstc_risk_score * 100).toFixed(1)}%`
                        : "N/A"}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}