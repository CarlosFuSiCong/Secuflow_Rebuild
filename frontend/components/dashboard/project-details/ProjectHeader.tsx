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
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-foreground">
              {project.name}
            </h2>
            <p className="text-muted-foreground mt-1">
              {project.description}
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              {project.repo_url}
            </p>
          </div>
          <DeleteProjectButton projectId={project.id} projectName={project.name} />
        </div>

        {/* Branch Selector */}
        <div className="space-y-3 mb-6">
          <label className="text-sm font-medium">Current Branch</label>
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
            <Alert className="border-orange-500 bg-orange-50 dark:bg-orange-950/20">
              <AlertTriangle className="h-4 w-4 text-orange-600" />
              <AlertDescription className="text-orange-700 dark:text-orange-300">
                <strong>Warning:</strong> Switching to <strong>{pendingBranch}</strong> will re-clone the repository 
                and re-run TNM and STC analysis. All existing analysis data will be replaced.
              </AlertDescription>
            </Alert>
          )}
        </div>

        {/* Statistics Grid - Show if TNM is complete or switching branch */}
        {(tnmComplete || isSwitchingBranch) && (
          <div className="border-t pt-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-4">Project Overview</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Members Card */}
              <div className="flex items-center gap-3 p-4 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800">
                <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900/20">
                  <Users className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Contributors</div>
                  {isSwitchingBranch && (project.members_count || 0) === 0 ? (
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                      <span className="text-sm text-muted-foreground">Analyzing...</span>
                    </div>
                  ) : (
                    <div className="text-xl font-bold">{project.members_count || 0}</div>
                  )}
                </div>
              </div>
              
              {/* Branches Card */}
              <div className="flex items-center gap-3 p-4 rounded-lg bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800">
                <div className="p-3 rounded-lg bg-green-100 dark:bg-green-900/20">
                  <GitBranch className="h-5 w-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Branches</div>
                  <div className="text-xl font-bold">{branchesCount}</div>
                </div>
              </div>
              
              {/* STC Score Card */}
              <div className="flex items-center gap-3 p-4 rounded-lg bg-purple-50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800">
                <div className="p-3 rounded-lg bg-purple-100 dark:bg-purple-900/20">
                  <BarChart3 className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">STC Score</div>
                  {isSwitchingBranch && !hasBasicAnalysis ? (
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin text-purple-600" />
                      <span className="text-sm text-muted-foreground">Computing...</span>
                    </div>
                  ) : (
                    <div className="text-xl font-bold">
                      {project.stc_risk_score !== null && project.stc_risk_score !== undefined
                        ? `${(project.stc_risk_score * 100).toFixed(1)}%`
                        : "N/A"}
                    </div>
                  )}
                </div>
              </div>
              
              {/* MC-STC Score Card */}
              <div className="flex items-center gap-3 p-4 rounded-lg bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-800">
                <div className="p-3 rounded-lg bg-orange-100 dark:bg-orange-900/20">
                  <AlertCircle className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">MC-STC Score</div>
                  {isSwitchingBranch && !hasFullAnalysis ? (
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin text-orange-600" />
                      <span className="text-sm text-muted-foreground">Computing...</span>
                    </div>
                  ) : (
                    <div className="text-xl font-bold">
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