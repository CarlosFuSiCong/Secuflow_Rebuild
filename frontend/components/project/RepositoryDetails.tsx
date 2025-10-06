"use client";

import { useEffect, useState } from "react";
import { GitBranch, Star, User, GitFork, Eye, Calendar } from "lucide-react";

const TEXT = {
  REPO_INFO_TITLE: "Repository Details",
  NO_DESCRIPTION: "No description available",
  LOADING: "Loading repository details...",
};

interface RepositoryDetailsProps {
  repoUrl: string;
  repoName?: string;
  repoOwner?: string;
  repoDescription?: string;
  stars?: number;
}

interface GitHubRepoData {
  name: string;
  full_name: string;
  description: string | null;
  stargazers_count: number;
  forks_count: number;
  watchers_count: number;
  language: string | null;
  created_at: string;
  updated_at: string;
  owner: {
    login: string;
    avatar_url: string;
  };
}

export function RepositoryDetails({
  repoUrl,
  repoName,
  repoOwner,
  repoDescription,
  stars,
}: RepositoryDetailsProps) {
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
          if (!data.message) { // Check if API call was successful
            setGithubData(data);
          }
        })
        .catch(err => console.error('Failed to fetch GitHub data:', err))
        .finally(() => setLoading(false));
    }
  }, [repoUrl]);

  // Use GitHub API data if available, otherwise use props
  const displayName = githubData?.name || repoName;
  const displayOwner = githubData?.owner.login || repoOwner;
  const displayDescription = githubData?.description || repoDescription;
  const displayStars = githubData?.stargazers_count ?? stars;
  const forks = githubData?.forks_count;
  const watchers = githubData?.watchers_count;
  const language = githubData?.language;
  const updatedAt = githubData?.updated_at;

  return (
    <div className="space-y-3">
      <h3 className="text-base font-semibold">{TEXT.REPO_INFO_TITLE}</h3>

      {loading && (
        <p className="text-sm text-muted-foreground italic">{TEXT.LOADING}</p>
      )}

      {/* Repository Name */}
      {displayName && (
        <div className="flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">{displayName}</span>
        </div>
      )}

      {/* Repository Owner */}
      {displayOwner && (
        <div className="flex items-center gap-2">
          <User className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">{displayOwner}</span>
        </div>
      )}

      {/* Repository Description */}
      {displayDescription && (
        <p className="text-sm text-muted-foreground">
          {displayDescription || TEXT.NO_DESCRIPTION}
        </p>
      )}

      {/* Repository Stats */}
      <div className="flex flex-wrap gap-4">
        {/* Stars */}
        {displayStars !== undefined && (
          <div className="flex items-center gap-1.5">
            <Star className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{displayStars}</span>
          </div>
        )}

        {/* Forks */}
        {forks !== undefined && (
          <div className="flex items-center gap-1.5">
            <GitFork className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{forks}</span>
          </div>
        )}

        {/* Watchers */}
        {watchers !== undefined && (
          <div className="flex items-center gap-1.5">
            <Eye className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{watchers}</span>
          </div>
        )}
      </div>

      {/* Language */}
      {language && (
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground">Language:</span>
          <span className="text-xs text-muted-foreground">{language}</span>
        </div>
      )}

      {/* Last Updated */}
      {updatedAt && (
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">
            Updated {new Date(updatedAt).toLocaleDateString()}
          </span>
        </div>
      )}
    </div>
  );
}
