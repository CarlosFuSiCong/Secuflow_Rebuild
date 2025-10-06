"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import { useAddProject } from "@/lib/hooks/useAddProject";
import { RepositoryInput } from "./RepositoryInput";
import { RepositoryDetails } from "./RepositoryDetails";
import { BranchSelector } from "./BranchSelector";

// Text constants
const TEXT = {
  SECTION_TITLE: "Add New Project",
  SECTION_DESCRIPTION: "Import a project from GitHub by providing the repository URL.",
  CARD_TITLE: "Import from GitHub",
  BUTTON_CREATE: "Import Project",
  BUTTON_CREATING: "Importing...",
  BUTTON_RESET: "Reset",
};

export function AddProjectSection() {
  const {
    repoUrl,
    setRepoUrl,
    isValidating,
    isCreating,
    validationError,
    createError,
    repoInfo,
    selectedBranch,
    setSelectedBranch,
    handleValidate,
    handleCreate,
    handleReset,
  } = useAddProject();

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
            onValidate={handleValidate}
            isValidating={isValidating}
            isDisabled={isValidating || isCreating || !!repoInfo}
            validationError={validationError}
          />

          {/* Repository Details - Shows after successful validation */}
          {repoInfo && repoInfo.valid && (
            <Collapsible open={!!repoInfo} className="space-y-4 border-t pt-4">
              <CollapsibleContent className="space-y-4">
                {/* Repository Details */}
                <RepositoryDetails
                  repoUrl={repoUrl}
                  repoName={repoInfo.repo_name}
                  repoOwner={repoInfo.repo_owner}
                  repoDescription={repoInfo.repo_description}
                  stars={repoInfo.stars}
                />

                {/* Branch Selection */}
                <BranchSelector
                  branches={repoInfo.branches || []}
                  selectedBranch={selectedBranch}
                  defaultBranch={repoInfo.default_branch}
                  onBranchChange={setSelectedBranch}
                  disabled={isCreating}
                />

                {/* Create Error */}
                {createError && (
                  <p className="text-sm text-destructive">{createError}</p>
                )}

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <Button
                    className="flex-1"
                    onClick={handleCreate}
                    disabled={isCreating}
                  >
                    {isCreating ? TEXT.BUTTON_CREATING : TEXT.BUTTON_CREATE}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleReset}
                    disabled={isCreating}
                  >
                    {TEXT.BUTTON_RESET}
                  </Button>
                </div>
              </CollapsibleContent>
            </Collapsible>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
