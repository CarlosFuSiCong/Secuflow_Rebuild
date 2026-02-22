"use client";

import { Badge } from "@/components/ui/badge";
import { TableRow, TableCell } from "@/components/ui/table";
import type { Project } from "@/lib/api/projects";
import { AlertTriangle, Shield, Users } from "lucide-react";
import { useRouter } from "next/navigation";
import { ProjectAnalysisStatus } from "./ProjectAnalysisStatus";

interface ProjectTableRowProps {
  project: Project;
}

// Helper function to format date
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString();
}

// Helper function to get risk level and color
function getRiskLevel(score?: number): { label: string; variant: "default" | "secondary" | "destructive" | "outline" } {
  if (score === undefined || score === null) {
    return { label: "N/A", variant: "secondary" };
  }

  if (score >= 80) {
    return { label: "High", variant: "destructive" };
  } else if (score >= 50) {
    return { label: "Medium", variant: "outline" };
  } else {
    return { label: "Low", variant: "default" };
  }
}

export function ProjectTableRow({ project }: ProjectTableRowProps) {
  const router = useRouter();
  const stcRisk = getRiskLevel(project.stc_risk_score);
  const mcstcRisk = getRiskLevel(project.mcstc_risk_score);

  // Check if project has completed analysis
  // Show data when last_risk_check_at exists (STC has run) OR when repository_path exists (TNM complete)
  const hasBasicAnalysis = !!project.last_risk_check_at;
  const tnmComplete = !!project.repository_path;  // TNM完成 = 仓库已克隆


  const handleRowClick = () => {
    router.push(`/dashboard?projectId=${project.id}`);
  };

  return (
    <TableRow
      key={project.id}
      className="cursor-pointer hover:bg-muted/50"
      onClick={handleRowClick}
    >
      <TableCell className="font-medium">
        <div className="flex flex-col gap-1">
          <span>{project.name}</span>
          <span className="text-xs text-muted-foreground truncate max-w-[200px]">
            {project.repo_url}
          </span>
          {/* Show analysis progress if not complete */}
          <ProjectAnalysisStatus
            projectId={project.id}
            autoRunSTC={project.auto_run_stc}
            autoRunMCSTC={project.auto_run_mcstc}
          />
          {/* Show contributor management hint when TNM complete but no STC */}
          {tnmComplete && !hasBasicAnalysis && (
            <span className="text-xs text-blue-600 dark:text-blue-400">
              💡 TNM complete - Contributors ready for role assignment
            </span>
          )}
        </div>
      </TableCell>

      {/* STC Risk Score */}
      <TableCell className="hidden lg:table-cell">
        {hasBasicAnalysis ? (
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-muted-foreground" />
            <Badge variant={stcRisk.variant}>
              {project.stc_risk_score !== undefined && project.stc_risk_score !== null
                ? `${(project.stc_risk_score * 100).toFixed(1)}%`
                : stcRisk.label}
            </Badge>
          </div>
        ) : tnmComplete ? (
          <span className="text-xs text-muted-foreground">Ready for analysis</span>
        ) : (
          <span className="text-xs text-muted-foreground">Analyzing...</span>
        )}
      </TableCell>

      {/* MCSTC Risk Score */}
      <TableCell className="hidden lg:table-cell">
        {hasBasicAnalysis ? (
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            <Badge variant={mcstcRisk.variant}>
              {project.mcstc_risk_score !== undefined && project.mcstc_risk_score !== null
                ? `${(project.mcstc_risk_score * 100).toFixed(1)}%`
                : mcstcRisk.label}
            </Badge>
          </div>
        ) : tnmComplete ? (
          <span className="text-xs text-muted-foreground">Ready for analysis</span>
        ) : (
          <span className="text-xs text-muted-foreground">Analyzing...</span>
        )}
      </TableCell>

      {/* Members Count */}
      <TableCell className="hidden md:table-cell">
        {hasBasicAnalysis ? (
          <div className="flex items-center gap-1.5">
            <Users className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">{project.members_count}</span>
          </div>
        ) : tnmComplete ? (
          <span className="text-xs text-muted-foreground">Ready</span>
        ) : (
          <span className="text-xs text-muted-foreground">-</span>
        )}
      </TableCell>

      {/* Last Analysis */}
      <TableCell className="hidden xl:table-cell text-sm text-muted-foreground">
        {hasBasicAnalysis
          ? project.last_risk_check_at ? formatDate(project.last_risk_check_at) : "Not analyzed"
          : tnmComplete ? "TNM complete" : "Analyzing..."}
      </TableCell>

      {/* Created Date */}
      <TableCell className="text-sm text-muted-foreground">
        {formatDate(project.created_at)}
      </TableCell>
    </TableRow>
  );
}
