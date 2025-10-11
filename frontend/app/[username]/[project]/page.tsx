"use client";

import { useParams } from "next/navigation";
import { ProfileNavbar } from "@/components/profile/ProfileNavbar";
import { ProjectDetails } from "@/components/dashboard/ProjectDetails";

export default function ProjectPage() {
  const params = useParams<{ username: string; project: string }>();

  // TODO: Fetch project by username and project name
  // For now, we'll use the project name as ID (you may need to convert this)
  const projectIdentifier = params.project;

  return (
    <div className="bg-background min-h-screen">
      <ProfileNavbar />

      <main className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
            <a href={`/${params.username}`} className="hover:text-foreground transition-colors">
              {params.username}
            </a>
            <span>/</span>
            <span className="text-foreground font-medium">{params.project}</span>
          </div>
        </div>

        {/* Project Details */}
        <ProjectDetails projectId={projectIdentifier} />
      </main>
    </div>
  );
}
