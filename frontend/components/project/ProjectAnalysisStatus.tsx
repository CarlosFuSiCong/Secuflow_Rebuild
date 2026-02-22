"use client";

import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Loader2, CheckCircle2, AlertCircle, ChevronDown } from "lucide-react";
import { useProjectAnalysisStatus } from "@/lib/hooks/useProjectAnalysisStatus";
import { AnalysisStepMini } from "./AnalysisStepMini";
import { useState } from "react";

interface ProjectAnalysisStatusProps {
  projectId: string;
  autoRunSTC?: boolean;
  autoRunMCSTC?: boolean;
}

export function ProjectAnalysisStatus({
  projectId,
  autoRunSTC = false,
  autoRunMCSTC = false,
}: ProjectAnalysisStatusProps) {
  const status = useProjectAnalysisStatus(projectId);
  const [isOpen, setIsOpen] = useState(false);

  // Don't show if completed
  if (status.isComplete) {
    return null;
  }

  // Don't show if in error state with progress 0 (likely API error)
  if (status.phase === "error" && status.progress === 0) {
    return null;
  }

  return (
    <div className="mt-2 space-y-2">
      {/* Progress bar */}
      <div className="flex items-center gap-2">
        <Progress value={status.progress} className="h-1.5 flex-1" />
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {status.progress}%
        </span>
      </div>

      {/* Status description */}
      <div className="flex items-center gap-2 text-xs">
        {status.phase === "cloning" && (
          <>
            <Loader2 className="h-3 w-3 animate-spin text-blue-600" />
            <span className="text-blue-600">{status.message}</span>
          </>
        )}
        {status.phase === "tnm_running" && (
          <>
            <Loader2 className="h-3 w-3 animate-spin text-purple-600" />
            <span className="text-purple-600">{status.message}</span>
          </>
        )}
        {status.phase === "stc_running" && (
          <>
            <Loader2 className="h-3 w-3 animate-spin text-indigo-600" />
            <span className="text-indigo-600">{status.message}</span>
          </>
        )}
        {status.phase === "mcstc_running" && (
          <>
            <Loader2 className="h-3 w-3 animate-spin text-violet-600" />
            <span className="text-violet-600">{status.message}</span>
          </>
        )}
        {status.phase === "completed" && (
          <>
            <CheckCircle2 className="h-3 w-3 text-green-600" />
            <span className="text-green-600">{status.message}</span>
          </>
        )}
        {status.phase === "error" && (
          <>
            <AlertCircle className="h-3 w-3 text-red-600" />
            <span className="text-red-600">{status.message}</span>
          </>
        )}
      </div>

      {/* Collapsible detailed steps */}
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 text-xs p-0 hover:bg-transparent"
          >
            View Details
            <ChevronDown
              className={`ml-1 h-3 w-3 transition-transform ${
                isOpen ? "rotate-180" : ""
              }`}
            />
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="pt-2 space-y-1">
          <AnalysisStepMini
            completed={status.progress > 40}
            active={status.phase === "cloning"}
            label="Repository cloned"
          />
          <AnalysisStepMini
            completed={status.progress > 70}
            active={status.phase === "tnm_running"}
            label="TNM analysis"
          />
          {autoRunSTC && (
            <AnalysisStepMini
              completed={status.progress > 90}
              active={status.phase === "stc_running"}
              label="STC analysis"
            />
          )}
          {autoRunMCSTC && (
            <AnalysisStepMini
              completed={status.progress === 100}
              active={status.phase === "mcstc_running"}
              label="MC-STC analysis"
            />
          )}
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}
