"use client";

import { useParams } from "next/navigation";
import { ProfileNavbar } from "@/components/profile/ProfileNavbar";
import { ProjectList } from "@/components/dashboard/ProjectList";

export default function UserPage() {
  const params = useParams<{ username: string }>();

  const handleProjectSelect = (projectId: string) => {
    // Navigate to project page with username/project format
    // TODO: Get project name from projectId
    window.location.href = `/${params.username}/${projectId}`;
  };

  return (
    <div className="bg-background min-h-screen">
      <ProfileNavbar />

      <main className="container mx-auto px-4 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">
            {params.username}&apos;s Projects
          </h1>
          <p className="text-muted-foreground mt-2">
            View all projects by @{params.username}
          </p>
        </div>

        {/* Project List */}
        <ProjectList onProjectSelect={handleProjectSelect} />
      </main>
    </div>
  );
}
