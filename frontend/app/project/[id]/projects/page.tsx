"use client";
import { ProfileNavbar } from "@/components/profile/ProfileNavbar";
import { Separator } from "@/components/ui/separator";
import { AddProjectSection } from "@/components/project/AddProjectSection";
import { ProjectsListSection } from "@/components/project/ProjectsListSection";
import { useProjects } from "@/lib/hooks/useProjects";

export default function ProjectsPage() {
  const projectsData = useProjects();

  const handleProjectAdded = () => {
    projectsData.refresh();
    projectsData.fetchAllProjects();
  };

  return (
    <div className="bg-background">
      <ProfileNavbar />
      <main>
        <div className="container mx-auto px-4 py-8">
          <div className="mb-8 pb-6 border-b border-border">
            <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground mb-1">
              Workspace
            </p>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              Projects
            </h1>
          </div>
          <div className="flex flex-col gap-8">
            <AddProjectSection onProjectAdded={handleProjectAdded} />
            <Separator />
            <ProjectsListSection useProjectsData={projectsData} />
          </div>
        </div>
      </main>
    </div>
  );
}
