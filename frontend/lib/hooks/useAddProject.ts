"use client";

import { useState } from "react";
import { validateRepository, createProject } from "@/lib/api";
import type { ValidateRepositoryData } from "@/lib/types/project";

export function useAddProject() {
  const [repoUrl, setRepoUrl] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [repoInfo, setRepoInfo] = useState<ValidateRepositoryData | null>(null);

  // Combined validate and create operation
  const handleValidateAndCreate = async () => {
    if (!repoUrl.trim()) {
      setError("Please enter a repository URL");
      return;
    }

    setIsProcessing(true);
    setError(null);
    setRepoInfo(null);

    try {
      // Step 1: Validate repository
      const response = await validateRepository(repoUrl);

      if (!response.data?.valid) {
        setError("Invalid repository URL or repository not found");
        return;
      }

      // Step 2: Create project automatically
      const projectName = repoUrl.split('/').pop()?.replace('.git', '') || 'project';

      let repoType = 'github';
      if (repoUrl.includes('gitlab')) {
        repoType = 'gitlab';
      } else if (repoUrl.includes('bitbucket')) {
        repoType = 'bitbucket';
      }

      await createProject({
        name: projectName,
        repo_url: repoUrl,
        repo_type: repoType,
      });

      // Success: show repository info
      setRepoInfo(response.data);

      return true;
    } catch (err: any) {
      const msg =
        err?.response?.data?.errorMessage ||
        err?.response?.data?.message ||
        err?.response?.data?.detail ||
        err?.message ||
        "Failed to validate and import repository";
      setError(msg);
      return false;
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setRepoUrl("");
    setRepoInfo(null);
    setError(null);
  };

  return {
    repoUrl,
    setRepoUrl,
    isProcessing,
    error,
    repoInfo,
    handleValidateAndCreate,
    handleReset,
  };
}
