"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { ProfileNavbar } from "@/components/profile/ProfileNavbar";
import { ProjectList } from "@/components/dashboard/ProjectList";
import { ProjectDetails } from "@/components/dashboard/ProjectDetails";
import { DASHBOARD_TEXT } from "@/app/dashboard/constants";

export default function UserDashboardPage() {
  const params = useParams<{ username: string }>();
  const [selectedProjectId, setSelectedProjectId] = useState<string | undefined>();

  const handleProjectSelect = (projectId: string) => {
    setSelectedProjectId(projectId);
    // Optional: You can also navigate to the project page directly
    // router.push(`/${params.username}/${projectId}`);
  };

  return (
    <div className="bg-background">
      <ProfileNavbar />

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8 pb-6 border-b border-border">
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1 font-medium tracking-wide uppercase">
            <a href={`/${params.username}`} className="hover:text-foreground transition-colors">
              {params.username}
            </a>
            <span>/</span>
            <span className="text-foreground">dashboard</span>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            {DASHBOARD_TEXT.PAGE_TITLE}
          </h1>
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
