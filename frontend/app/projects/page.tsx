"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser } from "@/lib/api";

export default function ProjectsRedirect() {
  const router = useRouter();

  useEffect(() => {
    const user = getCurrentUser();
    const userId = user?.id || 'user';
    router.replace(`/project/${userId}/projects`);
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <p className="text-muted-foreground">Redirecting...</p>
    </div>
  );
}
