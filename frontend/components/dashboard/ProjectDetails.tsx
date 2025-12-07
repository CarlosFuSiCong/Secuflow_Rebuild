"use client";

import { useState, useEffect } from "react";
import Card from "@/components/horizon/Card";
import { ProjectCharts } from "./ProjectCharts";
import { DASHBOARD_TEXT } from "@/app/dashboard/constants";
import type { ProjectDetailsProps } from "@/lib/types";
import { useProjects } from "@/lib/hooks/useProjects";
import { getProject, getProjectBranches } from "@/lib/api/projects";
import type { Project } from "@/lib/types/project";
import type { Branch } from "@/lib/types/project";
import {
  ProjectHeader,
  ProjectStats,
  BranchSelector,
  TeamMembersList,
  ProjectTabs,
  EmptyState,
  LoadingState,
  ErrorState
} from "./project-details";
import { STCMatrix } from "./project-details/STCMatrix";
import type { ProjectMember } from "@/lib/types";

export function ProjectDetails({ projectId }: ProjectDetailsProps) {
  // All useState hooks must be called before any early returns
  const [selectedBranch, setSelectedBranch] = useState("main");
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [branchesLoading, setBranchesLoading] = useState(false);

  const { allProjects } = useProjects();

  // Fetch project details when projectId changes
  useEffect(() => {
    if (!projectId) {
      setProject(null);
      setBranches([]);
      setBranchesLoading(false);
      return;
    }

    const fetchProjectDetails = async () => {
      setLoading(true);
      setError(null);

      try {
        const projectData = await getProject(projectId);
        setProject(projectData);
      } catch (err: any) {
        console.error("Failed to fetch project details:", err);
        setError(err?.response?.data?.message || "Failed to load project details");
      } finally {
        setLoading(false);
      }
    };

    fetchProjectDetails();
  }, [projectId]);

  // Fetch project branches when projectId changes
  useEffect(() => {
    if (!projectId) {
      setBranches([]);
      return;
    }

    const fetchBranches = async () => {
      setBranchesLoading(true);
      try {
        const branchesData = await getProjectBranches(projectId);
        setBranches(branchesData.branches || []);
      } catch (err) {
        console.error("Failed to fetch branches:", err);
        setBranches([]);
      } finally {
        setBranchesLoading(false);
      }
    };

    fetchBranches();
  }, [projectId]);

  if (!projectId) {
    return <EmptyState message={DASHBOARD_TEXT.NO_PROJECT_SELECTED} />;
  }

  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState error={error} />;
  }

  if (!project) {
    return <ErrorState error="Project not found" />;
  }

  // Prepare data for child components
  const members: ProjectMember[] = [
    // Mock members for now - in real app this would come from API
    { id: "1", name: "Project Owner", role: "Owner", joinedAt: project.created_at },
    { id: "2", name: "Developer", role: "Developer", joinedAt: project.created_at },
    { id: "3", name: "Contributor", role: "Contributor", joinedAt: project.created_at }
  ].slice(0, project.members_count || 3);

  const stats = {
    memberCount: project.members_count || 0,
    stcScore:
      project.stc_risk_score !== undefined && project.stc_risk_score !== null
        ? 1 - project.stc_risk_score
        : 0,
    riskLevel:
      project.stc_risk_score !== undefined && project.stc_risk_score !== null
        ? project.stc_risk_score >= 0.7
          ? "High"
          : project.stc_risk_score >= 0.4
          ? "Medium"
          : "Low"
        : "High",
  };

  const handleBranchChange = (branchName: string) => {
    setSelectedBranch(branchName);
  };


  return (
    <div className="space-y-6">
      {/* Project Header */}
      <ProjectHeader project={project} />

      {/* Overview Statistics */}
      <ProjectStats stats={stats} branchesCount={branches.length} />

      {/* Tabs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Tabs Navigation */}
        <div className="lg:col-span-1">
          <ProjectTabs />
        </div>

        {/* Right Column - Tab Content */}
        <div className="lg:col-span-2">
          {/* Overview Tab */}
          <Card>
            <div className="p-6">
              <h4 className="text-lg font-semibold text-foreground mb-4">
                {DASHBOARD_TEXT.TAB_OVERVIEW}
              </h4>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <BranchSelector
                    selectedBranch={selectedBranch}
                    branches={branches}
                    onBranchChange={handleBranchChange}
                  />
                </div>

                <TeamMembersList
                  members={members}
                  maxDisplay={3}
                  projectId={projectId}
                  onMemberAdded={() => {
                    // TODO: Refresh project data to get updated members
                    console.log("Member added, should refresh data");
                  }}
                />

                {/* STC Matrix Visualization */}
                <div className="mt-6">
                  <h4 className="text-lg font-semibold text-foreground mb-4">
                    Communication Congruence Matrix
                  </h4>
                  {project.latest_stc_result ? (
                    <STCMatrix analysisId={project.latest_stc_result.id} />
                  ) : (
                    <Card className="p-6 flex flex-col items-center justify-center text-center space-y-2 min-h-[300px]">
                      <div className="text-muted-foreground">
                        No STC analysis data available.
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Run an analysis to see the developer coordination matrix.
                      </p>
                    </Card>
                  )}
                </div>
              </div>
            </div>
          </Card>

          {/* Charts */}
          <div className="mt-6">
            <ProjectCharts projectId={projectId} branchName={selectedBranch} />
          </div>
        </div>
      </div>
    </div>
  );
}

