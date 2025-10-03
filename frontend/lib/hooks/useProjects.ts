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
      console.error("Error response:", err?.response);

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

  useEffect(() => {
    fetchProjects();
  }, [page, searchQuery, sort]);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setPage(1); // Reset to first page when searching
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
  };
}
