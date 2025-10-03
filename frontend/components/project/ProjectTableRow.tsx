"use client";

import { Badge } from "@/components/ui/badge";
import { TableRow, TableCell } from "@/components/ui/table";
import type { Project } from "@/lib/api/projects";
import { AlertTriangle, Shield, Users } from "lucide-react";

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
  const stcRisk = getRiskLevel(project.stc_risk_score);
  const mcstcRisk = getRiskLevel(project.mcstc_risk_score);

  return (
    <TableRow key={project.id} className="cursor-pointer hover:bg-muted/50">
      <TableCell className="font-medium">
        <div className="flex flex-col">
          <span>{project.name}</span>
          <span className="text-xs text-muted-foreground truncate max-w-[200px]">
            {project.repo_url}
          </span>
        </div>
      </TableCell>

      {/* STC Risk Score */}
      <TableCell className="hidden lg:table-cell">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-muted-foreground" />
          <Badge variant={stcRisk.variant}>
            {project.stc_risk_score !== undefined && project.stc_risk_score !== null
              ? `${project.stc_risk_score}%`
              : stcRisk.label}
          </Badge>
        </div>
      </TableCell>

      {/* MCSTC Risk Score */}
      <TableCell className="hidden lg:table-cell">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          <Badge variant={mcstcRisk.variant}>
            {project.mcstc_risk_score !== undefined && project.mcstc_risk_score !== null
              ? `${project.mcstc_risk_score}%`
              : mcstcRisk.label}
          </Badge>
        </div>
      </TableCell>

      {/* Members Count */}
      <TableCell className="hidden md:table-cell">
        <div className="flex items-center gap-1.5">
          <Users className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">{project.members_count}</span>
        </div>
      </TableCell>

      {/* Last Analysis */}
      <TableCell className="hidden xl:table-cell text-sm text-muted-foreground">
        {project.last_risk_check_at ? formatDate(project.last_risk_check_at) : "Not analyzed"}
      </TableCell>

      {/* Created Date */}
      <TableCell className="text-sm text-muted-foreground">
        {formatDate(project.created_at)}
      </TableCell>
    </TableRow>
  );
}
