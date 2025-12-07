"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { useAddProject } from "@/lib/hooks/useAddProject";
import { RepositoryInput } from "./RepositoryInput";
import { RepositoryDetails } from "./RepositoryDetails";

// Text constants
const TEXT = {
  SECTION_TITLE: "Add New Project",
  SECTION_DESCRIPTION: "Import a project from GitHub by providing the repository URL.",
  CARD_TITLE: "Import from GitHub",
  BUTTON_RESET: "Reset",
};

export function AddProjectSection({ onProjectAdded }: { onProjectAdded?: () => void }) {
  const {
    repoUrl,
    setRepoUrl,
    isProcessing,
    error,
    repoInfo,
    handleValidateAndCreate,
    handleReset,
  } = useAddProject();

  const handleImport = async () => {
    const success = await handleValidateAndCreate();
    if (success && onProjectAdded) {
      onProjectAdded();
    }
  };

  return (
    <section className="flex flex-col gap-4 lg:gap-6">
      <div className="space-y-1">
        <h2 className="text-xl font-semibold">{TEXT.SECTION_TITLE}</h2>
        <p className="text-muted-foreground text-sm lg:text-base">
          {TEXT.SECTION_DESCRIPTION}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">{TEXT.CARD_TITLE}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Repository URL Input */}
          <RepositoryInput
            repoUrl={repoUrl}
            onRepoUrlChange={setRepoUrl}
            onValidate={handleImport}
            isValidating={isProcessing}
            isDisabled={isProcessing || !!repoInfo}
            validationError={error}
          />

          {/* Repository Details - Shows after successful import */}
          {repoInfo && repoInfo.valid && (
            <div className="border-t pt-4">
              <div className="flex items-center justify-between gap-4">
                {/* Repository Details */}
                <div className="flex-1">
                  <RepositoryDetails repoUrl={repoUrl} />
                </div>

                {/* Reset Button */}
                <Button
                  variant="outline"
                  onClick={handleReset}
                  className="flex-shrink-0"
                >
                  {TEXT.BUTTON_RESET}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
