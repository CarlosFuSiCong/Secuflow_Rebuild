"use client";

import { useState, useEffect, useRef } from "react";
import { getProject } from "@/lib/api/projects";
import type { Project } from "@/lib/types/project";

type AnalysisPhase =
  | "cloning"
  | "tnm_running"
  | "stc_running"
  | "mcstc_running"
  | "completed"
  | "error";

export interface ProjectAnalysisStatusResult {
  phase: AnalysisPhase;
  progress: number;
  message: string;
  isComplete: boolean;
}

function deriveStatus(project: Project): ProjectAnalysisStatusResult {
  const autoRunSTC = project.auto_run_stc ?? false;
  const autoRunMCSTC = project.auto_run_mcstc ?? false;

  if (!project.repository_path) {
    return {
      phase: "cloning",
      progress: 15,
      message: "Cloning repository...",
      isComplete: false,
    };
  }

  const hasSTCResult = !!project.latest_stc_result;
  const hasMCSTCResult = !!project.latest_mcstc_result;

  const stcDone = !autoRunSTC || hasSTCResult;
  const mcstcDone = !autoRunMCSTC || hasMCSTCResult;

  if (stcDone && mcstcDone) {
    return {
      phase: "completed",
      progress: 100,
      message: "Analysis complete",
      isComplete: true,
    };
  }

  if (autoRunSTC && hasSTCResult && autoRunMCSTC && !hasMCSTCResult) {
    return {
      phase: "mcstc_running",
      progress: 80,
      message: "Running MC-STC analysis...",
      isComplete: false,
    };
  }

  if (autoRunSTC && !hasSTCResult) {
    return {
      phase: "stc_running",
      progress: 55,
      message: "Running STC analysis...",
      isComplete: false,
    };
  }

  return {
    phase: "tnm_running",
    progress: 35,
    message: "Running TNM analysis...",
    isComplete: false,
  };
}

const POLL_INTERVAL_MS = 3000;

export function useProjectAnalysisStatus(
  projectId: string
): ProjectAnalysisStatusResult {
  const [status, setStatus] = useState<ProjectAnalysisStatusResult>({
    phase: "cloning",
    progress: 10,
    message: "Initializing...",
    isComplete: false,
  });
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isCompleteRef = useRef(false);

  useEffect(() => {
    if (!projectId) return;

    const poll = async () => {
      if (isCompleteRef.current) return;
      try {
        const project = await getProject(projectId);
        const next = deriveStatus(project);
        setStatus(next);
        if (next.isComplete) {
          isCompleteRef.current = true;
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        }
      } catch {
        setStatus({
          phase: "error",
          progress: 0,
          message: "Failed to fetch project status",
          isComplete: false,
        });
      }
    };

    poll();
    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      isCompleteRef.current = false;
    };
  }, [projectId]);

  return status;
}
