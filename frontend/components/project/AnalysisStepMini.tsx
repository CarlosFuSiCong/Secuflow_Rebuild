"use client";

import { CheckCircle2, Loader2, Circle } from "lucide-react";

interface AnalysisStepMiniProps {
  label: string;
  completed?: boolean;
  active?: boolean;
}

export function AnalysisStepMini({
  label,
  completed = false,
  active = false,
}: AnalysisStepMiniProps) {
  return (
    <div className="flex items-center gap-2 text-xs">
      {completed ? (
        <CheckCircle2 className="h-3 w-3 text-green-600 flex-shrink-0" />
      ) : active ? (
        <Loader2 className="h-3 w-3 animate-spin text-blue-600 flex-shrink-0" />
      ) : (
        <Circle className="h-3 w-3 text-gray-300 flex-shrink-0" />
      )}
      <span
        className={
          completed
            ? "text-green-600"
            : active
            ? "text-foreground"
            : "text-muted-foreground"
        }
      >
        {label}
      </span>
    </div>
  );
}
