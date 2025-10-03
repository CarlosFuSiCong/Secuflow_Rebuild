"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const TEXT = {
  INPUT_PLACEHOLDER: "https://github.com/username/repository",
  INPUT_HINT: "Enter the full GitHub repository URL",
  BUTTON_VALIDATE: "Validate Repository",
  BUTTON_VALIDATING: "Validating...",
};

interface RepositoryInputProps {
  repoUrl: string;
  onRepoUrlChange: (value: string) => void;
  onValidate: () => void;
  isValidating: boolean;
  isDisabled: boolean;
  validationError?: string | null;
}

export function RepositoryInput({
  repoUrl,
  onRepoUrlChange,
  onValidate,
  isValidating,
  isDisabled,
  validationError,
}: RepositoryInputProps) {
  return (
    <div className="space-y-2">
      <div className="flex flex-col gap-2 md:flex-row md:gap-4">
        <div className="flex-1">
          <Input
            placeholder={TEXT.INPUT_PLACEHOLDER}
            className="w-full"
            value={repoUrl}
            onChange={(e) => onRepoUrlChange(e.target.value)}
            disabled={isDisabled}
          />
        </div>
        <Button
          className="md:w-auto"
          onClick={onValidate}
          disabled={isDisabled}
        >
          {isValidating ? TEXT.BUTTON_VALIDATING : TEXT.BUTTON_VALIDATE}
        </Button>
      </div>

      {validationError && (
        <p className="text-sm text-destructive">{validationError}</p>
      )}

      {!isDisabled && !validationError && (
        <p className="text-muted-foreground text-xs">{TEXT.INPUT_HINT}</p>
      )}
    </div>
  );
}
