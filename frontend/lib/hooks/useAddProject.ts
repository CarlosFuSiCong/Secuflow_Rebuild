"use client";

import { useState } from "react";
import { validateRepository, createProject, type Branch } from "@/lib/api";

interface RepositoryInfo {
  valid: boolean;
  repo_name?: string;
  repo_description?: string;
  repo_owner?: string;
  default_branch?: string;
  branches?: Branch[];
  stars?: number;
  repo_url?: string;
}

export function useAddProject() {
  const [repoUrl, setRepoUrl] = useState("");
  const [isValidating, setIsValidating] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [repoInfo, setRepoInfo] = useState<RepositoryInfo | null>(null);
  const [selectedBranch, setSelectedBranch] = useState<string>("");

  const handleValidate = async () => {
    if (!repoUrl.trim()) {
      setValidationError("Please enter a repository URL");
      return;
    }

    setIsValidating(true);
    setValidationError(null);
    setRepoInfo(null);

    try {
      const response = await validateRepository(repoUrl);

      if (response.data.valid) {
        setRepoInfo(response.data);
        setSelectedBranch(response.data.default_branch || "");
      } else {
        setValidationError("Invalid repository URL or repository not found");
      }
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message ||
        "Failed to validate repository";
      setValidationError(msg);
    } finally {
      setIsValidating(false);
    }
  };

  const handleCreate = async () => {
    if (!repoUrl || !repoInfo) return;

    setIsCreating(true);
    setCreateError(null);

    try {
      // Extract project name from repo_url or use repo_name from validation
      const projectName = repoInfo.repo_name || repoUrl.split('/').pop()?.replace('.git', '') || 'project';

      // Determine repo_type from URL
      let repoType = 'github';
      if (repoUrl.includes('gitlab')) {
        repoType = 'gitlab';
      } else if (repoUrl.includes('bitbucket')) {
        repoType = 'bitbucket';
      }

      await createProject({
        name: projectName,
        description: repoInfo.repo_description || '',
        repo_url: repoUrl,
        repo_type: repoType,
      });

      // Reset form on success
      setRepoUrl("");
      setRepoInfo(null);
      setSelectedBranch("");

      return true;
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.response?.data?.errorMessage ||
        err?.message ||
        "Failed to create project";
      setCreateError(msg);
      return false;
    } finally {
      setIsCreating(false);
    }
  };

  const handleReset = () => {
    setRepoInfo(null);
    setValidationError(null);
    setCreateError(null);
    setSelectedBranch("");
  };

  return {
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
  };
}
