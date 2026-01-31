"use client";

import { useState, useEffect } from "react";
import { listProjects, type Project, type ListProjectsParams } from "@/lib/api";

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [searchQuery, setSearchQuery] = useState("");
  const [sort, setSort] = useState("-created_at");

  // For frontend search - all projects
  const [allProjects, setAllProjects] = useState<Project[]>([]);
  const [allProjectsLoading, setAllProjectsLoading] = useState(false);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);

    try {
      const params: ListProjectsParams = {
        q: searchQuery || undefined,
        sort,
        include_deleted: false,
        page,
        page_size: pageSize,
      };

      const response = await listProjects(params);

      console.log("API Response:", response); // Debug log

      if (response && response.results) {
        setProjects(response.results);
        setTotalCount(response.count);
      } else {
        console.error("API Response failed:", response);
        setError("Failed to fetch projects");
      }
    } catch (err: any) {
      console.error("Fetch projects error:", err);
      if (err?.response) {
        console.error("Error response:", err.response);
      }

      const msg =
        err?.response?.data?.errorMessage ||
        err?.response?.data?.message ||
        err?.message ||
        "Failed to fetch projects";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllProjects = async () => {
    setAllProjectsLoading(true);
    setError(null);

    try {
      // Get first page to determine total count
      const firstPageResponse = await listProjects({
        sort,
        include_deleted: false,
        page: 1,
        page_size: 100, // Use larger page size for all projects
      });

      if (firstPageResponse && firstPageResponse.results) {
        setAllProjects(firstPageResponse.results);
        setTotalCount(firstPageResponse.count);

        // If there are more pages, fetch them all
        const totalPages = Math.ceil(firstPageResponse.count / 100);
        if (totalPages > 1) {
          const allResults = [...firstPageResponse.results];

          // Fetch remaining pages in parallel
          const pagePromises = [];
          for (let i = 2; i <= totalPages; i++) {
            pagePromises.push(
              listProjects({
                sort,
                include_deleted: false,
                page: i,
                page_size: 100,
              })
            );
          }

          const remainingResults = await Promise.all(pagePromises);
          remainingResults.forEach(response => {
            if (response && response.results) {
              allResults.push(...response.results);
            }
          });

          setAllProjects(allResults);
        }
      } else {
        setError("Failed to fetch all projects");
      }
    } catch (err: any) {
      console.error("Fetch all projects error:", err);
      const msg =
        err?.response?.data?.errorMessage ||
        err?.response?.data?.message ||
        err?.message ||
        "Failed to fetch all projects";
      setError(msg);
    } finally {
      setAllProjectsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, searchQuery, sort]);

  // Load all projects for frontend search
  useEffect(() => {
    fetchAllProjects();
  }, []); // Only load once on mount

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setPage(1); // Reset to first page when searching
  };

  // Frontend search function
  const searchProjectsLocally = (query: string) => {
    if (!query.trim()) {
      return allProjects;
    }

    const lowerQuery = query.toLowerCase();
    return allProjects.filter(project =>
      project.name.toLowerCase().includes(lowerQuery) ||
      project.repo_url.toLowerCase().includes(lowerQuery)
    );
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handleSort = (newSort: string) => {
    setSort(newSort);
    setPage(1); // Reset to first page when sorting
  };

  const refresh = () => {
    fetchProjects();
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  return {
    projects,
    loading,
    error,
    totalCount,
    page,
    pageSize,
    totalPages,
    searchQuery,
    handleSearch,
    handlePageChange,
    handleSort,
    refresh,
    // For frontend search
    allProjects,
    allProjectsLoading,
    searchProjectsLocally,
    fetchAllProjects,
  };
}
