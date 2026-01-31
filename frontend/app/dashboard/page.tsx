"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { ProfileNavbar } from "@/components/profile/ProfileNavbar";
import { ProjectDetails } from "@/components/dashboard/ProjectDetails";
import { DASHBOARD_TEXT } from "./constants";

export default function DashboardPage() {
  const searchParams = useSearchParams();
  const projectIdFromUrl = searchParams.get("projectId");
  const [selectedProjectId, setSelectedProjectId] = useState<string | undefined>(
    projectIdFromUrl || undefined
  );

  useEffect(() => {
    if (projectIdFromUrl) {
      setSelectedProjectId(projectIdFromUrl);
    }
  }, [projectIdFromUrl]);

  return (
    <div className="bg-background">
      <ProfileNavbar />

      <main className="container mx-auto px-4 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">
            {DASHBOARD_TEXT.PAGE_TITLE}
          </h1>
          <p className="text-muted-foreground mt-2">
            View your project details, team members, branches, and analytics
          </p>
        </div>

        {/* Project Details - Full Width */}
        <div className="w-full">
          <ProjectDetails projectId={selectedProjectId} />
        </div>
      </main>
    </div>
  );
}

