"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, ArrowRight, Info, Circle, CheckCircle2 } from "lucide-react";
import type { Branch } from "@/lib/types/project";
import type { AnalysisOptions } from "@/lib/hooks/useAddProject";

const TEXT = {
  TITLE: "Project Configuration",
  LABEL_NAME: "Project Name",
  LABEL_BRANCH: "Branch",
  LABEL_DESCRIPTION: "Description (Optional)",
  PLACEHOLDER_NAME: "Enter project name",
  PLACEHOLDER_DESCRIPTION: "Add a description for this project",
  BUTTON_CREATE: "Create Project",
  BUTTON_CREATING: "Creating...",
  STATUS_VALIDATING: "Validating repository...",
  STATUS_CREATING: "Creating project record...",
  ANALYSIS_TITLE: "Analysis Options",
  ANALYSIS_DESCRIPTION: "Select analyses to run automatically after project creation",
  TNM_LABEL: "TNM Analysis (Required)",
  TNM_DESCRIPTION: "Analyzes repository structure and ownership (runs in background)",
  STC_LABEL: "STC Analysis",
  STC_DESCRIPTION: "Calculates socio-technical congruence (1-5s, runs after TNM)",
  MCSTC_LABEL: "MC-STC Analysis",
  MCSTC_DESCRIPTION: "Multi-class coordination analysis (requires role setup)",
  MCSTC_WARNING: "MC-STC requires participant roles to be set. You can configure them after project creation in Project Settings.",
};

export interface ProjectConfigData {
  name: string;
  branch: string;
  description: string;
}

interface ProjectConfigurationProps {
  branches: Branch[];
  defaultBranch: string;
  defaultName: string;
  onCreateProject: (config: ProjectConfigData) => void;
  isCreating: boolean;
  error?: string | null;
  analysisOptions: AnalysisOptions;
  onAnalysisOptionsChange: (options: AnalysisOptions) => void;
}

export function ProjectConfiguration({
  branches,
  defaultBranch,
  defaultName,
  onCreateProject,
  isCreating,
  error,
  analysisOptions,
  onAnalysisOptionsChange,
}: ProjectConfigurationProps) {
  const [projectName, setProjectName] = useState(defaultName);
  const [selectedBranch, setSelectedBranch] = useState(defaultBranch);
  const [description, setDescription] = useState("");

  // Update defaults when they change
  useEffect(() => {
    setProjectName(defaultName);
  }, [defaultName]);

  useEffect(() => {
    setSelectedBranch(defaultBranch);
  }, [defaultBranch]);

  const handleCreate = () => {
    if (!projectName.trim()) {
      return;
    }

    onCreateProject({
      name: projectName.trim(),
      branch: selectedBranch,
      description: description.trim(),
    });
  };

  const isValid = projectName.trim().length > 0;

  return (
    <div className="space-y-4 border-t pt-4">
      {/* Title */}
      <h3 className="text-base font-semibold">{TEXT.TITLE}</h3>

      {/* Form */}
      <div className="space-y-4">
        {/* Project Name */}
        <div className="space-y-2">
          <Label htmlFor="project-name">{TEXT.LABEL_NAME}</Label>
          <Input
            id="project-name"
            placeholder={TEXT.PLACEHOLDER_NAME}
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            disabled={isCreating}
            required
          />
        </div>

        {/* Branch Selection */}
        <div className="space-y-2">
          <Label htmlFor="branch-select">{TEXT.LABEL_BRANCH}</Label>
          <Select
            value={selectedBranch}
            onValueChange={setSelectedBranch}
            disabled={isCreating}
          >
            <SelectTrigger id="branch-select">
              <SelectValue placeholder="Select a branch" />
            </SelectTrigger>
            <SelectContent>
              {branches.map((branch) => (
                <SelectItem key={branch.name} value={branch.name}>
                  {branch.name}
                  {branch.name === defaultBranch && " (default)"}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Description */}
        <div className="space-y-2">
          <Label htmlFor="description">{TEXT.LABEL_DESCRIPTION}</Label>
          <Input
            id="description"
            placeholder={TEXT.PLACEHOLDER_DESCRIPTION}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={isCreating}
          />
        </div>

        {/* Analysis Options */}
        <div className="space-y-3 border-t pt-4">
          <div>
            <h4 className="font-medium text-sm">{TEXT.ANALYSIS_TITLE}</h4>
            <p className="text-xs text-muted-foreground mt-1">
              {TEXT.ANALYSIS_DESCRIPTION}
            </p>
          </div>

          <div className="space-y-3">
            {/* TNM - Always checked, disabled */}
            <div className="flex items-start gap-3">
              <Checkbox checked disabled className="mt-1" />
              <div className="flex-1 space-y-1">
                <Label className="text-sm font-normal cursor-default">
                  {TEXT.TNM_LABEL}
                </Label>
                <p className="text-xs text-muted-foreground">
                  {TEXT.TNM_DESCRIPTION}
                </p>
              </div>
            </div>

            {/* STC - Optional */}
            <div className="flex items-start gap-3">
              <Checkbox
                checked={analysisOptions.runSTC}
                onCheckedChange={(checked) =>
                  onAnalysisOptionsChange({
                    ...analysisOptions,
                    runSTC: checked === true,
                  })
                }
                disabled={isCreating}
                className="mt-1"
              />
              <div className="flex-1 space-y-1">
                <Label className="text-sm font-normal cursor-pointer">
                  {TEXT.STC_LABEL}
                </Label>
                <p className="text-xs text-muted-foreground">
                  {TEXT.STC_DESCRIPTION}
                </p>
              </div>
            </div>

            {/* MC-STC - Optional */}
            <div className="flex items-start gap-3">
              <Checkbox
                checked={analysisOptions.runMCSTC}
                onCheckedChange={(checked) =>
                  onAnalysisOptionsChange({
                    ...analysisOptions,
                    runMCSTC: checked === true,
                  })
                }
                disabled={isCreating}
                className="mt-1"
              />
              <div className="flex-1 space-y-1">
                <Label className="text-sm font-normal cursor-pointer">
                  {TEXT.MCSTC_LABEL}
                </Label>
                <p className="text-xs text-muted-foreground">
                  {TEXT.MCSTC_DESCRIPTION}
                </p>
              </div>
            </div>
          </div>

          {/* MC-STC Warning */}
          {analysisOptions.runMCSTC && (
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription className="text-xs">
                {TEXT.MCSTC_WARNING}
              </AlertDescription>
            </Alert>
          )}
        </div>

        {/* Creation progress indicators */}
        {isCreating && (
          <div className="mt-4 space-y-2 border rounded-lg p-3 bg-muted/30">
            <div className="flex items-center gap-2 text-sm">
              <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0" />
              <span className="text-muted-foreground">Validate repository</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Loader2 className="h-4 w-4 animate-spin text-blue-600 flex-shrink-0" />
              <span className="font-medium">{TEXT.STATUS_CREATING}</span>
            </div>
          </div>
        )}

        {/* Error message */}
        {error && !isCreating && (
          <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-md">
            {error}
          </div>
        )}

        {/* Create Button */}
        <div className="flex justify-end">
          <Button
            onClick={handleCreate}
            disabled={!isValid || isCreating}
            className="min-w-[160px]"
          >
            {isCreating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {TEXT.BUTTON_CREATING}
              </>
            ) : (
              <>
                {TEXT.BUTTON_CREATE}
                <ArrowRight className="ml-2 h-4 w-4" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
