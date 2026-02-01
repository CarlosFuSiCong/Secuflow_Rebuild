"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Search, Save, RefreshCw, AlertCircle, ChevronLeft, ChevronRight } from "lucide-react";
import {
  getProjectContributorsClassification,
  getFunctionalRoleChoices,
  updateContributorClassifications,
  type ProjectContributor,
  type FunctionalRoleChoice,
  type ContributorUpdate,
} from "@/lib/api/contributors";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface ContributorRoleManagementProps {
  projectId: string;
}

export function ContributorRoleManagement({ projectId }: ContributorRoleManagementProps) {
  const [contributors, setContributors] = useState<ProjectContributor[]>([]);
  const [roleChoices, setRoleChoices] = useState<FunctionalRoleChoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState(""); // For debounced search
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [changes, setChanges] = useState<Map<string, ContributorUpdate>>(new Map());
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const totalPages = Math.ceil(totalCount / pageSize);

  // Load role choices
  useEffect(() => {
    const loadRoleChoices = async () => {
      try {
        const choices = await getFunctionalRoleChoices();
        setRoleChoices(choices);
      } catch (err) {
        console.error("Failed to load role choices:", err);
      }
    };
    loadRoleChoices();
  }, []);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput);
      setCurrentPage(1); // Reset to first page on search
    }, 500); // 500ms debounce

    return () => clearTimeout(timer);
  }, [searchInput]);

  // Load contributors when filters or pagination changes
  useEffect(() => {
    loadContributors();
  }, [projectId, search, roleFilter, currentPage, pageSize]);

  const loadContributors = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getProjectContributorsClassification(projectId, {
        search: search || undefined,
        role: roleFilter !== "all" ? roleFilter : undefined,
        page: currentPage,
        page_size: pageSize,
      });
      setContributors(response.results);
      setTotalCount(response.count);
    } catch (err: any) {
      console.error("Failed to load contributors:", err);
      setError(err?.response?.data?.message || "Failed to load contributors");
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = (contributorId: string, role: string) => {
    const updated = new Map(changes);
    const existing = updated.get(contributorId) || { id: contributorId };
    updated.set(contributorId, { ...existing, functional_role: role });
    setChanges(updated);

    // Update local state
    setContributors(
      contributors.map((c) =>
        c.id === contributorId ? { ...c, functional_role: role } : c
      )
    );
  };

  const handleCoreChange = (contributorId: string, isCore: boolean) => {
    const updated = new Map(changes);
    const existing = updated.get(contributorId) || { id: contributorId };
    updated.set(contributorId, { ...existing, is_core_contributor: isCore });
    setChanges(updated);

    // Update local state
    setContributors(
      contributors.map((c) =>
        c.id === contributorId ? { ...c, is_core_contributor: isCore } : c
      )
    );
  };

  const handleSave = async () => {
    if (changes.size === 0) return;

    setSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const updates = Array.from(changes.values());
      const result = await updateContributorClassifications(projectId, updates);
      setSuccessMessage(`Successfully updated ${result.updated_count} contributors`);
      setChanges(new Map());
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      console.error("Failed to save changes:", err);
      setError(err?.response?.data?.message || "Failed to save changes");
    } finally {
      setSaving(false);
    }
  };

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case "developer":
        return "default";
      case "security":
        return "destructive";
      case "ops":
        return "outline";
      default:
        return "secondary";
    }
  };

  if (loading) {
    return (
      <Card className="p-8">
        <div className="flex items-center justify-center">
          <RefreshCw className="h-6 w-6 animate-spin text-primary" />
          <span className="ml-2">Loading contributors...</span>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with actions */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Contributor Roles</h3>
          <p className="text-sm text-muted-foreground">
            Set functional roles for MC-STC analysis ({totalCount} total)
          </p>
        </div>
        <div className="flex items-center gap-2">
          {changes.size > 0 && (
            <span className="text-sm text-muted-foreground">
              {changes.size} unsaved changes
            </span>
          )}
          <Button
            onClick={handleSave}
            disabled={saving || changes.size === 0}
            size="sm"
          >
            {saving ? (
              <RefreshCw className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            Save Changes
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by login or email..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={roleFilter} onValueChange={(value) => {
          setRoleFilter(value);
          setCurrentPage(1);
        }}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Roles</SelectItem>
            {roleChoices.map((choice) => (
              <SelectItem key={choice.value} value={choice.value}>
                {choice.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={pageSize.toString()} onValueChange={(value) => {
          setPageSize(parseInt(value));
          setCurrentPage(1);
        }}>
          <SelectTrigger className="w-[120px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="10">10 / page</SelectItem>
            <SelectItem value="25">25 / page</SelectItem>
            <SelectItem value="50">50 / page</SelectItem>
            <SelectItem value="100">100 / page</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline" size="icon" onClick={loadContributors}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Messages */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {successMessage && (
        <Alert>
          <AlertDescription>{successMessage}</AlertDescription>
        </Alert>
      )}

      {/* Contributors table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="border-b">
              <tr className="text-sm text-muted-foreground">
                <th className="text-left p-3 font-medium">Contributor</th>
                <th className="text-left p-3 font-medium">Activity</th>
                <th className="text-left p-3 font-medium">Role</th>
                <th className="text-left p-3 font-medium">Core</th>
              </tr>
            </thead>
            <tbody>
              {contributors.length === 0 ? (
                <tr>
                  <td colSpan={4} className="p-8 text-center text-muted-foreground">
                    {totalCount === 0 
                      ? "No contributors found. TNM analysis may not be complete yet."
                      : "No contributors match the current filters."}
                  </td>
                </tr>
              ) : (
                contributors.map((contributor) => (
                  <tr key={contributor.id} className="border-b hover:bg-muted/50">
                    <td className="p-3">
                      <div className="flex flex-col">
                        <span className="font-medium">{contributor.contributor_login}</span>
                        <span className="text-xs text-muted-foreground">
                          {contributor.contributor_email}
                        </span>
                      </div>
                    </td>
                    <td className="p-3">
                      <div className="flex flex-col text-sm">
                        <span>{contributor.commits_count} commits</span>
                        <span className="text-xs text-muted-foreground">
                          {contributor.total_modifications} modifications
                        </span>
                      </div>
                    </td>
                    <td className="p-3">
                      <Select
                        value={contributor.functional_role}
                        onValueChange={(value) => handleRoleChange(contributor.id, value)}
                      >
                        <SelectTrigger className="w-[150px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {roleChoices.map((choice) => (
                            <SelectItem key={choice.value} value={choice.value}>
                              {choice.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </td>
                    <td className="p-3">
                      <Checkbox
                        checked={contributor.is_core_contributor}
                        onCheckedChange={(checked) =>
                          handleCoreChange(contributor.id, checked === true)
                        }
                      />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t">
            <div className="text-sm text-muted-foreground">
              Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} contributors
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }
                  
                  return (
                    <Button
                      key={pageNum}
                      variant={currentPage === pageNum ? "default" : "outline"}
                      size="sm"
                      onClick={() => setCurrentPage(pageNum)}
                      className="w-8 h-8 p-0"
                    >
                      {pageNum}
                    </Button>
                  );
                })}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Info */}
      <div className="text-sm text-muted-foreground">
        <p>
          💡 Tip: Set roles before running MC-STC analysis to get role-specific coordination
          insights.
        </p>
      </div>
    </div>
  );
}
