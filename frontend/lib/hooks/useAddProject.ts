"use client";

import { useState } from "react";
import { validateRepository, createProject } from "@/lib/api";
import type { ValidateRepositoryData } from "@/lib/types/project";

type ImportStep = 'input' | 'validating' | 'validated' | 'creating' | 'completed';

export function useAddProject() {
  const [repoUrl, setRepoUrl] = useState("");
  const [currentStep, setCurrentStep] = useState<ImportStep>('input');
  const [error, setError] = useState<string | null>(null);
  const [repoInfo, setRepoInfo] = useState<ValidateRepositoryData | null>(null);

  const isProcessing = currentStep === 'validating' || currentStep === 'creating';

  // Step 1: Validate repository only
  const handleValidate = async () => {
    if (!repoUrl.trim()) {
      setError("Please enter a repository URL");
      return false;
    }

    setCurrentStep('validating');
    setError(null);
    setRepoInfo(null);

    try {
      const response = await validateRepository(repoUrl);

      if (!response.data?.valid) {
        setError("Invalid repository URL or repository not found");
        setCurrentStep('input');
        return false;
      }

      // Success: move to validated state
      setRepoInfo(response.data);
      setCurrentStep('validated');
      return true;
    } catch (err: any) {
      const msg =
        err?.response?.data?.errorMessage ||
        err?.response?.data?.message ||
        err?.response?.data?.detail ||
        err?.message ||
        "Failed to validate repository";
      setError(msg);
      setCurrentStep('input');
      return false;
    }
  };

  // Step 2: Create project after validation
  const handleCreate = async (projectName?: string, description?: string, branch?: string) => {
    if (!repoInfo || currentStep !== 'validated') {
      setError("Please validate the repository first");
      return false;
    }

    setCurrentStep('creating');
    setError(null);

    try {
      // Use provided name or extract from URL
      const name = projectName || repoUrl.split('/').pop()?.replace('.git', '') || 'project';

      let repoType = 'github';
      if (repoUrl.includes('gitlab')) {
        repoType = 'gitlab';
      } else if (repoUrl.includes('bitbucket')) {
        repoType = 'bitbucket';
      }

      await createProject({
        name,
        repo_url: repoUrl,
        repo_type: repoType,
        description: description || undefined,
      });

      setCurrentStep('completed');
      return true;
    } catch (err: any) {
      const msg =
        err?.response?.data?.errorMessage ||
        err?.response?.data?.message ||
        err?.response?.data?.detail ||
        err?.message ||
        "Failed to create project";
      setError(msg);
      setCurrentStep('validated');
      return false;
    }
  };

  const handleReset = () => {
    setRepoUrl("");
    setRepoInfo(null);
    setError(null);
    setCurrentStep('input');
  };

  return {
    repoUrl,
    setRepoUrl,
    currentStep,
    isProcessing,
    error,
    repoInfo,
    handleValidate,
    handleCreate,
    handleReset,
  };
}
