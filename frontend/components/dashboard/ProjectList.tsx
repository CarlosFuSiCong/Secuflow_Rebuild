"use client";

import { useState, useEffect } from "react";
import Card from "@/components/horizon/Card";
import { DASHBOARD_TEXT } from "@/app/dashboard/constants";
import type { ProjectListProps } from "@/lib/types";
import { useProjects } from "@/lib/hooks/useProjects";
import { enhanceProject, type EnhancedProject } from "@/lib/utils/project-helpers";
import { getProjectBranches } from "@/lib/api/projects";

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
        return "bg-destructive/10 text-destructive";
      case "Medium":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300";
      case "Low":
        return "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300";
      default:
        return "bg-muted text-muted-foreground";
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
          <div className="relative">
            <input
              type="text"
              placeholder={DASHBOARD_TEXT.PROJECT_SEARCH_PLACEHOLDER}
              value={searchQuery}
              onChange={(e) => handleLocalSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent bg-background text-foreground"
              disabled={loading}
            />
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {(loading || allProjectsLoading || loadingBranches) && (
          <div className="text-center py-8 text-muted-foreground">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-2"></div>
            {loadingBranches ? "Loading project details..." : "Loading projects..."}
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
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h4 className="font-semibold text-foreground text-sm">
                        {project.name}
                      </h4>
                      <p className="text-xs text-muted-foreground truncate mt-1">
                        {project.repo_url}
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskBadgeVariant(project.riskLevel)}`}>
                      {project.riskLevel}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center space-x-4">
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                        {project.members_count || 0}
                      </span>
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                        </svg>
                        {loadingBranches ? "..." : (project.branchCount || 0)}
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

