"use client";

import { Button } from "@/components/ui/button";
import { CheckCircle2, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";

const TEXT = {
  TITLE: "Project Created Successfully!",
  MESSAGE: "Your project has been imported and is ready to use.",
  BUTTON_VIEW: "View Project",
  BUTTON_ADD_ANOTHER: "Add Another Project",
};

interface ProjectCreatedSuccessProps {
  projectId?: string;
  projectName: string;
  onReset: () => void;
}

export function ProjectCreatedSuccess({
  projectId,
  projectName,
  onReset,
}: ProjectCreatedSuccessProps) {
  const router = useRouter();

  const handleViewProject = () => {
    if (projectId) {
      router.push(`/projects/${projectId}`);
    }
  };

  return (
    <div className="space-y-4 border-t pt-4">
      {/* Success Icon and Message */}
      <div className="flex items-start gap-3">
        <CheckCircle2 className="h-6 w-6 text-green-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-green-600">{TEXT.TITLE}</h3>
          <p className="text-sm text-muted-foreground">
            {TEXT.MESSAGE}
          </p>
          <p className="text-sm font-medium">
            Project: <span className="text-primary">{projectName}</span>
          </p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        {projectId && (
          <Button onClick={handleViewProject} className="flex-1">
            {TEXT.BUTTON_VIEW}
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        )}
        <Button
          variant="outline"
          onClick={onReset}
          className={projectId ? "flex-1" : "w-full"}
        >
          {TEXT.BUTTON_ADD_ANOTHER}
        </Button>
      </div>
    </div>
  );
}
