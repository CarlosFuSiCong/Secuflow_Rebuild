"use client";

import { Button } from "@/components/ui/button";
import { ReactNode } from "react";

interface FormContainerProps {
  children: ReactNode;
  onSubmit: () => void;
  loading?: boolean;
  error?: string | null;
  message?: string | null;
  submitText?: string;
  loadingText?: string;
}

export function FormContainer({
  children,
  onSubmit,
  loading = false,
  error = null,
  message = null,
  submitText = "Save",
  loadingText = "Saving...",
}: FormContainerProps) {
  return (
    <div className="col-span-8 space-y-4 md:space-y-6 lg:col-span-4">
      {children}
      <div className="flex items-center gap-3">
        <Button onClick={onSubmit} disabled={loading}>
          {loading ? loadingText : submitText}
        </Button>
        {message && (
          <span className="text-sm text-emerald-600 dark:text-emerald-400">
            {message}
          </span>
        )}
        {error && (
          <span className="text-sm text-destructive">
            {error}
          </span>
        )}
      </div>
    </div>
  );
}