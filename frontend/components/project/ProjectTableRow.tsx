"use client";

import { TableRow, TableCell } from "@/components/ui/table";
import type { Project } from "@/lib/api/projects";
import { AlertTriangle, Shield, Users } from "lucide-react";
import { useRouter } from "next/navigation";
import { ProjectAnalysisStatus } from "./ProjectAnalysisStatus";

interface ProjectTableRowProps {
  project: Project;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString();
}

function getScoreDisplay(score?: number): { label: string; className: string } {
  if (score === undefined || score === null) {
    return { label: "N/A", className: "text-muted-foreground border border-border bg-transparent" };
  }
  const pct = score * 100;
  if (pct > 70) {
    return { label: "Good", className: "text-green-600 border border-green-300 bg-transparent dark:text-green-400 dark:border-green-700" };
  } else if (pct > 30) {
    return { label: "Fair", className: "text-orange-500 border border-orange-300 bg-transparent dark:text-orange-400 dark:border-orange-700" };
  } else {
    return { label: "Poor", className: "text-red-600 border border-red-300 bg-transparent dark:text-red-400 dark:border-red-700" };
  }
}

export function ProjectTableRow({ project }: ProjectTableRowProps) {
  const router = useRouter();
  const stcDisplay = getScoreDisplay(project.stc_risk_score);
  const mcstcDisplay = getScoreDisplay(project.mcstc_risk_score);

  const hasBasicAnalysis = !!project.last_risk_check_at;
  const tnmComplete = !!project.repository_path && (project.members_count ?? 0) > 0;

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
          <ProjectAnalysisStatus
            projectId={project.id}
            autoRunSTC={project.auto_run_stc}
            autoRunMCSTC={project.auto_run_mcstc}
          />
          {tnmComplete && !hasBasicAnalysis && (
            <span className="text-xs text-muted-foreground">
              TNM complete — contributors ready for role assignment
            </span>
          )}
        </div>
      </TableCell>

      {/* STC Score */}
      <TableCell className="hidden lg:table-cell">
        {hasBasicAnalysis ? (
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-muted-foreground" />
            <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${stcDisplay.className}`}>
              {project.stc_risk_score != null
                ? `${(project.stc_risk_score * 100).toFixed(1)}%`
                : stcDisplay.label}
            </span>
          </div>
        ) : tnmComplete ? (
          <span className="text-xs text-muted-foreground">Ready for analysis</span>
        ) : (
          <span className="text-xs text-muted-foreground">Analyzing…</span>
        )}
      </TableCell>

      {/* MC-STC Score */}
      <TableCell className="hidden lg:table-cell">
        {hasBasicAnalysis ? (
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${mcstcDisplay.className}`}>
              {project.mcstc_risk_score != null
                ? `${(project.mcstc_risk_score * 100).toFixed(1)}%`
                : mcstcDisplay.label}
            </span>
          </div>
        ) : tnmComplete ? (
          <span className="text-xs text-muted-foreground">Ready for analysis</span>
        ) : (
          <span className="text-xs text-muted-foreground">Analyzing…</span>
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
          <span className="text-xs text-muted-foreground">—</span>
        )}
      </TableCell>

      {/* Last Analysis */}
      <TableCell className="hidden xl:table-cell text-sm text-muted-foreground">
        {hasBasicAnalysis
          ? project.last_risk_check_at ? formatDate(project.last_risk_check_at) : "Not analyzed"
          : tnmComplete ? "TNM complete" : "Analyzing…"}
      </TableCell>

      {/* Created Date */}
      <TableCell className="text-sm text-muted-foreground">
        {formatDate(project.created_at)}
      </TableCell>
    </TableRow>
  );
}
