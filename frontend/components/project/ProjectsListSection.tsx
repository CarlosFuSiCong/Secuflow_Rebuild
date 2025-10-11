"use client";

import { ProjectSearchBar } from "./ProjectSearchBar";
import { ProjectTable } from "./ProjectTable";
import { useProjects } from "@/lib/hooks/useProjects";

const TEXT = {
  SECTION_TITLE: "Your Projects",
  SECTION_DESCRIPTION: "View and manage all your imported GitHub projects.",
  LOADING: "Loading projects...",
  ERROR: "Failed to load projects",
  NO_PROJECTS: "No projects found",
};

export function ProjectsListSection() {
  const {
    projects,
    loading,
    error,
    page,
    totalPages,
    searchQuery,
    handleSearch,
    handlePageChange,
  } = useProjects();


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
        onSearchChange={handleSearch}
      />

      {loading && (
        <p className="text-center text-muted-foreground py-8">{TEXT.LOADING}</p>
      )}

      {error && (
        <p className="text-center text-destructive py-8">{error}</p>
      )}

      {!loading && !error && projects.length === 0 && (
        <p className="text-center text-muted-foreground py-8">{TEXT.NO_PROJECTS}</p>
      )}

      {!loading && !error && projects.length > 0 && (
        <ProjectTable
          projects={projects}
          currentPage={page}
          totalPages={totalPages}
          onPageChange={handlePageChange}
        />
      )}
    </section>
  );
}
