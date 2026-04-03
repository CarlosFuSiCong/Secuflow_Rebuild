"use client";

import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
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
    <div className="space-y-5">
      {children}
      <div className="flex items-center gap-4 pt-1">
        <Button onClick={onSubmit} disabled={loading} size="sm">
          {loading ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin mr-2" />
              {loadingText}
            </>
          ) : (
            submitText
          )}
        </Button>
        {message && (
          <span className="text-xs text-green-600">{message}</span>
        )}
        {error && (
          <span className="text-xs text-destructive">{error}</span>
        )}
      </div>
    </div>
  );
}
