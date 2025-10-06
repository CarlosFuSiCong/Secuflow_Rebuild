"use client";

import { useEffect, useState } from "react";
import { GitBranch, Star, User, GitFork } from "lucide-react";

const TEXT = {
  REPO_INFO_TITLE: "Repository Details",
  LOADING: "Loading...",
};

interface RepositoryDetailsProps {
  repoUrl: string;
}

interface GitHubRepoData {
  name: string;
  full_name: string;
  stargazers_count: number;
  forks_count: number;
  owner: {
    login: string;
  };
}

export function RepositoryDetails({ repoUrl }: RepositoryDetailsProps) {
  const [githubData, setGithubData] = useState<GitHubRepoData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Extract owner and repo name from GitHub URL
    const githubMatch = repoUrl.match(/github\.com[\/:](.+?)\/(.+?)(\.git)?$/);

    if (githubMatch) {
      const [, owner, repo] = githubMatch;
      const cleanRepo = repo.replace('.git', '');

      setLoading(true);
      fetch(`https://api.github.com/repos/${owner}/${cleanRepo}`)
        .then(res => res.json())
        .then(data => {
          if (!data.message) {
            setGithubData(data);
          }
        })
        .catch(err => console.error('Failed to fetch GitHub data:', err))
        .finally(() => setLoading(false));
    }
  }, [repoUrl]);

  return (
    <div className="flex items-center gap-4">
      {/* Title */}
      <h3 className="text-base font-semibold">{TEXT.REPO_INFO_TITLE}</h3>

      {/* Details */}
      {loading ? (
        <p className="text-sm text-muted-foreground italic">{TEXT.LOADING}</p>
      ) : (
        <div className="flex items-center gap-4 flex-wrap">
          {/* Repository Name */}
          {githubData?.name && (
            <div className="flex items-center gap-1.5">
              <GitBranch className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">{githubData.name}</span>
            </div>
          )}

          {/* Repository Owner */}
          {githubData?.owner.login && (
            <div className="flex items-center gap-1.5">
              <User className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{githubData.owner.login}</span>
            </div>
          )}

          {/* Stars */}
          {githubData?.stargazers_count !== undefined && (
            <div className="flex items-center gap-1.5">
              <Star className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{githubData.stargazers_count}</span>
            </div>
          )}

          {/* Forks */}
          {githubData?.forks_count !== undefined && (
            <div className="flex items-center gap-1.5">
              <GitFork className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{githubData.forks_count}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
