"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { searchUsers } from "@/lib/api/users";
import { addProjectMember } from "@/lib/api/projects";
import type { AddMembersProps } from "@/lib/types";
import type { User } from "@/lib/types/user";
import { UserPlus, Loader2 } from "lucide-react";
import { toast } from "sonner";

const USER_ROLES = [
  { value: "Developer", label: "Developer" },
  { value: "Contributor", label: "Contributor" },
  { value: "Viewer", label: "Viewer" },
];

export function AddMembers({ projectId, existingMembers = [], onMemberAdded }: AddMembersProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [selectedRole, setSelectedRole] = useState("Contributor");
  const [isSearching, setIsSearching] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  // Search users when query changes
  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      if (searchQuery.trim().length >= 2) {
        handleSearchUsers();
      } else {
        setSearchResults([]);
        setShowDropdown(false);
        setHasSearched(false);
      }
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [searchQuery]);

  const handleSearchUsers = async () => {
    setIsSearching(true);
    setError(null);
    setHasSearched(false);

    try {
      const response = await searchUsers({ search: searchQuery, page_size: 10 });
      if (response.data) {
        setSearchResults(response.data.results);
        setShowDropdown(true);
        setHasSearched(true);
      }
    } catch (err: any) {
      console.error("Failed to search users:", err);
      setError("Failed to search users. Please try again.");
      setSearchResults([]);
      setShowDropdown(false);
      setHasSearched(false);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectUser = (user: User) => {
    setSelectedUserId(user.id);
    setSearchQuery(user.username);
    setShowDropdown(false);
  };

  // Check if user is already a member
  const isUserAlreadyMember = (userId: string): boolean => {
    return existingMembers.some(member => member.id === userId);
  };

  const handleAddMember = async () => {
    if (!selectedUserId) {
      setError("Please select a user");
      return;
    }

    if (!selectedRole) {
      setError("Please select a role");
      return;
    }

    // Check if user is already a member
    if (isUserAlreadyMember(selectedUserId)) {
      setError("This user is already a member of the project");
      return;
    }

    setIsAdding(true);
    setError(null);

    try {
      await addProjectMember(projectId, {
        user_id: selectedUserId,
        role: selectedRole,
      });

      toast.success("Member added successfully!");
      setSearchQuery("");
      setSelectedUserId("");
      setSelectedRole("Contributor");
      setSearchResults([]);

      if (onMemberAdded) {
        onMemberAdded();
      }
    } catch (err: any) {
      console.error("Failed to add member:", err);
      const msg = err?.response?.data?.message || "Failed to add member to project";
      toast.error(msg);
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <UserPlus className="w-5 h-5 text-muted-foreground" />
        <h3 className="text-lg font-semibold text-foreground">Add Member</h3>
      </div>

      <div className="space-y-3">
        {/* User Search Input */}
        <div className="relative">
          <label className="block text-sm font-medium text-foreground mb-2">
            Search User
          </label>
          <Input
            type="text"
            placeholder="Enter username..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
            className="w-full"
          />
          {isSearching && (
            <div className="absolute right-3 top-10">
              <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
            </div>
          )}

          {/* Search Results Dropdown */}
          {showDropdown && (
            <div className="absolute z-50 w-full mt-1 bg-popover border border-border rounded-md shadow-lg max-h-60 overflow-y-auto">
              {searchResults.length > 0 ? (
                searchResults.map((user) => {
                  const isAlreadyMember = isUserAlreadyMember(user.id);
                  return (
                    <button
                      key={user.id}
                      onClick={() => handleSelectUser(user)}
                      disabled={isAlreadyMember}
                      className={`w-full px-3 py-2 text-left transition-colors flex items-center justify-between ${
                        isAlreadyMember
                          ? "opacity-50 cursor-not-allowed bg-muted/50"
                          : "hover:bg-accent"
                      }`}
                    >
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-foreground">
                          {user.username}
                        </span>
                        {user.email && (
                          <span className="text-xs text-muted-foreground">
                            {user.email}
                          </span>
                        )}
                      </div>
                      {isAlreadyMember && (
                        <span className="text-xs text-muted-foreground">
                          Already member
                        </span>
                      )}
                    </button>
                  );
                })
              ) : hasSearched ? (
                <div className="px-3 py-4 text-center text-sm text-muted-foreground">
                  No users found for "{searchQuery}"
                </div>
              ) : null}
            </div>
          )}
        </div>

        {/* Role Selection */}
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Role
          </label>
          <Select value={selectedRole} onValueChange={setSelectedRole}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select a role" />
            </SelectTrigger>
            <SelectContent>
              {USER_ROLES.map((role) => (
                <SelectItem key={role.value} value={role.value}>
                  {role.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Inline validation error */}
        {error && (
          <div className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-md">
            {error}
          </div>
        )}

        {/* Add Button */}
        <Button
          onClick={handleAddMember}
          disabled={!selectedUserId || !selectedRole || isAdding}
          className="w-full"
        >
          {isAdding ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
              Adding...
            </>
          ) : (
            <>
              <UserPlus className="w-4 h-4 mr-2" />
              Add Member
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
