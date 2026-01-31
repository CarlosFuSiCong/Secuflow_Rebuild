"use client";

import { useState, useEffect } from "react";
import { ProjectSearchBar } from "./ProjectSearchBar";
import { ProjectTable } from "./ProjectTable";
import { useProjects } from "@/lib/hooks/useProjects";
import { enhanceProject, type EnhancedProject } from "@/lib/utils/project-helpers";
import { getProjectBranches } from "@/lib/api/projects";

const TEXT = {
  SECTION_TITLE: "My Projects",
  SECTION_DESCRIPTION: "View and manage all your imported GitHub projects.",
  LOADING: "Loading projects...",
  ERROR: "Failed to load projects",
  NO_PROJECTS: "No projects found",
};

export function ProjectsListSection({
  useProjectsData,
}: {
  useProjectsData: ReturnType<typeof useProjects>;
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [enhancedProjects, setEnhancedProjects] = useState<EnhancedProject[]>([]);
  const [loadingBranches, setLoadingBranches] = useState(false);

  const {
    allProjects,
    loading,
    error,
    allProjectsLoading,
    searchProjectsLocally,
    handleSearch,
  } = useProjectsData;

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
    // Debounce search to avoid excessive API calls while typing
    setTimeout(() => {
      handleSearch(query);
    }, 300);
  };

  // Filter projects locally based on search query
  const filteredProjects = searchProjectsLocally(searchQuery);

  // Get pagination info from filtered results
  const totalFilteredProjects = filteredProjects.length;
  const totalPages = Math.ceil(totalFilteredProjects / 10); // Assuming 10 items per page
  const currentPageProjects = filteredProjects.slice(0, 10); // Show first 10 items


  return (
    <section className="flex flex-col gap-4 lg:gap-6">
      <div className="space-y-1">
        <h2 className="text-xl font-semibold">{TEXT.SECTION_TITLE}</h2>
        <p className="text-muted-foreground text-sm lg:text-base">
          {TEXT.SECTION_DESCRIPTION}
        </p>
      </div>

      <ProjectSearchBar
        searchQuery={searchQuery}
        onSearchChange={handleLocalSearch}
      />

      {(loading || allProjectsLoading || loadingBranches) && (
        <p className="text-center text-muted-foreground py-8">
          {loadingBranches ? "Loading project details..." : TEXT.LOADING}
        </p>
      )}

      {error && !loading && !allProjectsLoading && (
        <p className="text-center text-destructive py-8">{error}</p>
      )}

      {!loading && !allProjectsLoading && !error && filteredProjects.length === 0 && (
        <p className="text-center text-muted-foreground py-8">
          {searchQuery ? "No projects found matching your search" : TEXT.NO_PROJECTS}
        </p>
      )}

      {!loading && !allProjectsLoading && !error && filteredProjects.length > 0 && (
        <ProjectTable
          projects={currentPageProjects}
          currentPage={1}
          totalPages={totalPages}
          onPageChange={(page) => {
            // For now, just scroll to top or handle pagination differently
            // Since we're showing filtered results, pagination might need adjustment
            console.log("Page change:", page);
          }}
        />
      )}
    </section>
  );
}
