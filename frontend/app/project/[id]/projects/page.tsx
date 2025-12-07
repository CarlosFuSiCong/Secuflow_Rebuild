"use client";
import { ProfileNavbar } from "@/components/profile/ProfileNavbar";
import { Separator } from "@/components/ui/separator";
import { AddProjectSection } from "@/components/project/AddProjectSection";
import { ProjectsListSection } from "@/components/project/ProjectsListSection";
import { useParams } from "next/navigation";
import { useProjects } from "@/lib/hooks/useProjects";

export default function ProjectsPage() {
  const params = useParams();
  const projectsData = useProjects();

  const handleProjectAdded = () => {
    projectsData.refresh();
    projectsData.fetchAllProjects();
  };

  return (
    <div className="bg-background">
      <ProfileNavbar />
      <main>
        <div className="container mx-auto flex flex-col gap-6 p-4 lg:gap-8 lg:p-6">
          <AddProjectSection onProjectAdded={handleProjectAdded} />
          <Separator />
          <ProjectsListSection useProjectsData={projectsData} />
        </div>
      </main>
    </div>
  );
}
