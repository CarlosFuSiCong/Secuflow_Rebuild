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
import { ProjectConfiguration, type ProjectConfigData } from "./ProjectConfiguration";
import { ProjectCreatedSuccess } from "./ProjectCreatedSuccess";

// Text constants
const TEXT = {
  SECTION_TITLE: "Add New Project",
  SECTION_DESCRIPTION: "Import a project from GitHub by providing the repository URL.",
  CARD_TITLE: "Import from GitHub",
  BUTTON_RESET: "Reset",
  STEP_1: "Step 1: Validate Repository",
  STEP_2: "Step 2: Configure & Create Project",
  STEP_COMPLETE: "✓ Completed",
};

export function AddProjectSection({ onProjectAdded }: { onProjectAdded?: () => void }) {
  const {
    repoUrl,
    setRepoUrl,
    currentStep,
    isProcessing,
    error,
    repoInfo,
    handleValidate,
    handleCreate,
    handleReset,
  } = useAddProject();

  const isValidating = currentStep === 'validating';
  const isValidated = currentStep === 'validated';
  const isCreating = currentStep === 'creating';
  const isCompleted = currentStep === 'completed';

  const handleCreateProject = async (config: ProjectConfigData) => {
    const success = await handleCreate(config.name, config.description, config.branch);
    if (success && onProjectAdded) {
      onProjectAdded();
    }
  };

  // Get default project name from URL
  const defaultProjectName = repoUrl.split('/').pop()?.replace('.git', '') || '';

  // Determine current step indicator
  const getStepIndicator = () => {
    if (isCompleted) {
      return TEXT.STEP_COMPLETE;
    } else if (isValidated || isCreating) {
      return TEXT.STEP_2;
    } else {
      return TEXT.STEP_1;
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
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold">{TEXT.CARD_TITLE}</CardTitle>
            {/* Step indicator */}
            <span className="text-sm text-muted-foreground">
              {getStepIndicator()}
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Step 1: Repository URL Input */}
          <RepositoryInput
            repoUrl={repoUrl}
            onRepoUrlChange={setRepoUrl}
            onValidate={handleValidate}
            isValidating={isValidating}
            isDisabled={isProcessing || isValidated || isCompleted}
            validationError={error}
            isValidated={isValidated || isCompleted}
          />

          {/* Step 1 Result: Repository Details */}
          {repoInfo && repoInfo.valid && (isValidated || isCreating || isCompleted) && (
            <div className="border-t pt-4">
              <div className="flex items-center justify-between gap-4">
                {/* Repository Details */}
                <div className="flex-1">
                  <RepositoryDetails repoUrl={repoUrl} />
                </div>

                {/* Reset Button - Only show if not completed */}
                {!isCompleted && (
                  <Button
                    variant="outline"
                    onClick={handleReset}
                    className="flex-shrink-0"
                    disabled={isCreating}
                  >
                    {TEXT.BUTTON_RESET}
                  </Button>
                )}
              </div>
            </div>
          )}

          {/* Step 2: Project Configuration */}
          {isValidated && repoInfo && repoInfo.branches && (
            <ProjectConfiguration
              branches={repoInfo.branches}
              defaultBranch={repoInfo.default_branch}
              defaultName={defaultProjectName}
              onCreateProject={handleCreateProject}
              isCreating={isCreating}
              error={error}
            />
          )}

          {/* Step 3: Success Message */}
          {isCompleted && (
            <ProjectCreatedSuccess
              projectName={defaultProjectName}
              onReset={handleReset}
            />
          )}
        </CardContent>
      </Card>
    </section>
  );
}
