"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ProfileNavbar } from "@/components/profile/ProfileNavbar";
import { ProjectDetails } from "@/components/dashboard/ProjectDetails";
import { DASHBOARD_TEXT } from "./constants";

function DashboardContent() {
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
    <main className="container mx-auto px-4 py-8">
      <div className="mb-8 pb-6 border-b border-border">
        <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground mb-1">
          Overview
        </p>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          {DASHBOARD_TEXT.PAGE_TITLE}
        </h1>
      </div>

      <div className="w-full">
        <ProjectDetails projectId={selectedProjectId} />
      </div>
    </main>
  );
}

export default function DashboardPage() {
  return (
    <div className="bg-background">
      <ProfileNavbar />
      <Suspense fallback={<main className="container mx-auto px-4 py-6" />}>
        <DashboardContent />
      </Suspense>
    </div>
  );
}

