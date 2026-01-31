"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, ArrowRight } from "lucide-react";
import type { Branch } from "@/lib/types/project";

const TEXT = {
  TITLE: "Project Configuration",
  LABEL_NAME: "Project Name",
  LABEL_BRANCH: "Branch",
  LABEL_DESCRIPTION: "Description (Optional)",
  PLACEHOLDER_NAME: "Enter project name",
  PLACEHOLDER_DESCRIPTION: "Add a description for this project",
  BUTTON_CREATE: "Create Project",
  BUTTON_CREATING: "Creating...",
  STATUS_CREATING: "Creating project...",
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
}

export function ProjectConfiguration({
  branches,
  defaultBranch,
  defaultName,
  onCreateProject,
  isCreating,
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

        {/* Status message when creating */}
        {isCreating && (
          <div className="flex items-center gap-2 text-sm text-blue-600">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>{TEXT.STATUS_CREATING}</span>
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
