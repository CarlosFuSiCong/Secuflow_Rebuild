"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ProfileNavbar } from "@/components/profile/ProfileNavbar";
import { ProjectList } from "@/components/dashboard/ProjectList";
import { ProjectDetails } from "@/components/dashboard/ProjectDetails";
import { DASHBOARD_TEXT } from "@/app/dashboard/constants";

export default function UserDashboardPage() {
  const params = useParams<{ username: string }>();
  const router = useRouter();
  const [selectedProjectId, setSelectedProjectId] = useState<string | undefined>();

  const handleProjectSelect = (projectId: string) => {
    setSelectedProjectId(projectId);
    // Optional: You can also navigate to the project page directly
    // router.push(`/${params.username}/${projectId}`);
  };

  return (
    <div className="bg-background">
      <ProfileNavbar />

      <main className="container mx-auto px-4 py-6">
        <div className="mb-8">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
            <a href={`/${params.username}`} className="hover:text-foreground transition-colors">
              {params.username}
            </a>
            <span>/</span>
            <span className="text-foreground font-medium">dashboard</span>
          </div>
          <h1 className="text-3xl font-bold text-foreground">
            {DASHBOARD_TEXT.PAGE_TITLE}
          </h1>
          <p className="text-muted-foreground mt-2">
            Manage your projects, team members, branches, and view analytics
          </p>
        </div>

        <div className="grid grid-cols-12 gap-6">
          {/* Left Column - Project List */}
          <div className="col-span-12 lg:col-span-4">
            <ProjectList
              selectedProjectId={selectedProjectId}
              onProjectSelect={handleProjectSelect}
            />
          </div>

          {/* Right Column - Project Details */}
          <div className="col-span-12 lg:col-span-8">
            <ProjectDetails projectId={selectedProjectId} />
          </div>
        </div>
      </main>
    </div>
  );
}
