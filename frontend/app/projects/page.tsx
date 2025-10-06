"use client";
import { ProfileNavbar } from "@/components/profile/ProfileNavbar";
import { Separator } from "@/components/ui/separator";
import { AddProjectSection } from "@/components/project/AddProjectSection";
import { ProjectsListSection } from "@/components/project/ProjectsListSection";

export default function ProjectsPage() {
  return (
    <div className="bg-background">
      <ProfileNavbar />
      <main>
        <div className="container mx-auto flex flex-col gap-6 p-4 lg:gap-8 lg:p-6">
          <AddProjectSection />
          <Separator />
          <ProjectsListSection />
        </div>
      </main>
    </div>
  );
}
