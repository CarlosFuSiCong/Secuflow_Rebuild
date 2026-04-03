"use client";

import { useState, useEffect } from "react";
import Card from "@/components/horizon/Card";
import { Input } from "@/components/ui/input";
import { DASHBOARD_TEXT } from "@/app/dashboard/constants";
import type { ProjectListProps } from "@/lib/types";
import { useProjects } from "@/lib/hooks/useProjects";
import { enhanceProject, type EnhancedProject } from "@/lib/utils/project-helpers";
import { getProjectBranches } from "@/lib/api/projects";
import { Users, GitBranch, Loader2 } from "lucide-react";

export function ProjectList({ selectedProjectId, onProjectSelect }: ProjectListProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [enhancedProjects, setEnhancedProjects] = useState<EnhancedProject[]>([]);
  const [loadingBranches, setLoadingBranches] = useState(false);
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);

  const {
    allProjects,
    loading,
    error,
    allProjectsLoading,
    searchProjectsLocally,
  } = useProjects();

  // Enhance projects with branch count and calculated fields
  useEffect(() => {
    const enhanceProjectsWithBranches = async () => {
      if (!allProjects || allProjects.length === 0) {
        setEnhancedProjects([]);
        return;
      }

      setLoadingBranches(true);
      const enhanced = await Promise.all(
        allProjects.map(async (project) => {
          try {
            const branchesData = await getProjectBranches(project.id);
            return enhanceProject(project, branchesData.branches.length);
          } catch {
            // If branches fetch fails, still enhance with available data
            return enhanceProject(project);
          }
        })
      );
      setEnhancedProjects(enhanced);
      setLoadingBranches(false);
    };

    enhanceProjectsWithBranches();
  }, [allProjects]);

  // Handle local search query - use debounce for better UX
  const handleLocalSearch = (query: string) => {
    setSearchQuery(query);

    // Clear previous timeout
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    // Set new timeout for debounced search
    const timeout = setTimeout(() => {
      // No need to call API, just update local state
      // The search will be handled by filteredProjects below
    }, 300);

    setSearchTimeout(timeout);
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
    };
  }, [searchTimeout]);

  // Filter projects locally based on search query
  // For frontend search, we need to enhance the filtered results
  const filteredProjectIds = searchProjectsLocally(searchQuery).map(p => p.id);
  const filteredProjects = enhancedProjects.filter(project =>
    filteredProjectIds.includes(project.id)
  );

  const getRiskBadgeVariant = (riskLevel: string) => {
    switch (riskLevel) {
      case "High":
        return "text-red-600 border border-red-300 bg-transparent dark:text-red-400 dark:border-red-700";
      case "Medium":
        return "text-orange-500 border border-orange-300 bg-transparent dark:text-orange-400 dark:border-orange-700";
      case "Low":
        return "text-green-600 border border-green-300 bg-transparent dark:text-green-400 dark:border-green-700";
      default:
        return "text-muted-foreground border border-border bg-transparent";
    }
  };

  return (
    <Card extra="h-full">
      <div className="p-6">
        <div className="mb-6">
          <h3 className="text-xl font-bold text-foreground mb-4">
            {DASHBOARD_TEXT.PROJECT_LIST_TITLE}
          </h3>

          {/* Search Input */}
          <Input
            type="text"
            placeholder={DASHBOARD_TEXT.PROJECT_SEARCH_PLACEHOLDER}
            value={searchQuery}
            onChange={(e) => handleLocalSearch(e.target.value)}
            disabled={loading}
          />
        </div>

        {/* Loading State */}
        {(loading || allProjectsLoading || loadingBranches) && (
          <div className="flex flex-col items-center py-10 text-muted-foreground gap-2">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-xs">{loadingBranches ? "Loading project details..." : "Loading projects..."}</span>
          </div>
        )}

        {/* Error State */}
        {error && !loading && !allProjectsLoading && (
          <div className="text-center py-8 text-destructive">
            <p className="mb-2">Failed to load projects</p>
            <p className="text-sm text-muted-foreground">{error}</p>
          </div>
        )}

        {/* Project List */}
        {!loading && !allProjectsLoading && !error && (
          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {filteredProjects.map((project) => {
              const isSelected = selectedProjectId === project.id;
              const stcScore = project.stcScore;

              return (
                <div
                  key={project.id}
                  onClick={() => onProjectSelect?.(project.id)}
                  className={`p-4 rounded-lg cursor-pointer transition-all duration-200 border ${
                    isSelected
                      ? "bg-primary/5 border-primary"
                      : "bg-card border-border hover:bg-accent"
                  }`}
                >
                  <div className="flex items-start justify-between mb-2 gap-2">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-foreground text-sm truncate">
                        {project.name}
                      </h4>
                      <p className="text-xs text-muted-foreground truncate mt-1" title={project.repo_url}>
                        {project.repo_url}
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium flex-shrink-0 ${getRiskBadgeVariant(project.riskLevel)}`}>
                      {project.riskLevel}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center space-x-4">
                      <span className="flex items-center gap-1">
                        <Users className="w-3.5 h-3.5" />
                        {project.members_count || 0}
                      </span>
                      <span className="flex items-center gap-1">
                        <GitBranch className="w-3.5 h-3.5" />
                        {loadingBranches ? "…" : (project.branchCount || 0)}
                      </span>
                    </div>
                    <span className="font-medium text-primary">
                      STC: {stcScore !== null ? stcScore.toFixed(2) : "N/A"}
                    </span>
                  </div>
                </div>
              );
            })}

            {filteredProjects.length === 0 && !loadingBranches && (
              <div className="text-center py-8 text-muted-foreground">
                {searchQuery ? "No projects found matching your search" : DASHBOARD_TEXT.MSG_NO_DATA}
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}

