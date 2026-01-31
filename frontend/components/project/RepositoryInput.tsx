"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CheckCircle2, Loader2 } from "lucide-react";

const TEXT = {
  INPUT_PLACEHOLDER: "https://github.com/username/repository",
  INPUT_HINT: "Enter the full GitHub repository URL",
  BUTTON_VALIDATE: "Validate Repository",
  BUTTON_VALIDATING: "Validating...",
  STATUS_VALIDATING: "Validating repository...",
};

interface RepositoryInputProps {
  repoUrl: string;
  onRepoUrlChange: (value: string) => void;
  onValidate: () => void;
  isValidating: boolean;
  isDisabled: boolean;
  validationError?: string | null;
  isValidated?: boolean;
}

export function RepositoryInput({
  repoUrl,
  onRepoUrlChange,
  onValidate,
  isValidating,
  isDisabled,
  validationError,
  isValidated = false,
}: RepositoryInputProps) {
  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-2 md:flex-row md:gap-4">
        <div className="flex-1">
          <Input
            placeholder={TEXT.INPUT_PLACEHOLDER}
            className="w-full"
            value={repoUrl}
            onChange={(e) => onRepoUrlChange(e.target.value)}
            disabled={isDisabled}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !isDisabled) {
                onValidate();
              }
            }}
          />
        </div>
        <Button
          className="md:w-auto"
          onClick={onValidate}
          disabled={isDisabled || !repoUrl.trim()}
        >
          {isValidating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {TEXT.BUTTON_VALIDATING}
            </>
          ) : (
            TEXT.BUTTON_VALIDATE
          )}
        </Button>
      </div>

      {/* Status messages */}
      {isValidating && (
        <div className="flex items-center gap-2 text-sm text-blue-600">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>{TEXT.STATUS_VALIDATING}</span>
        </div>
      )}

      {isValidated && !validationError && (
        <div className="flex items-center gap-2 text-sm text-green-600">
          <CheckCircle2 className="h-4 w-4" />
          <span>Repository validated successfully!</span>
        </div>
      )}

      {validationError && (
        <p className="text-sm text-destructive">{validationError}</p>
      )}

      {!isDisabled && !validationError && !isValidating && !isValidated && (
        <p className="text-muted-foreground text-xs">{TEXT.INPUT_HINT}</p>
      )}
    </div>
  );
}
