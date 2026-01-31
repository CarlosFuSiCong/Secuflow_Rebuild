"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { AddMembers } from "./AddMembers";
import type { TeamMembersListProps } from "@/lib/types";
import { UserPlus, ChevronDown, ChevronUp } from "lucide-react";

export function TeamMembersList({ members, maxDisplay = 3, projectId, onMemberAdded }: TeamMembersListProps) {
  const [showAddMember, setShowAddMember] = useState(false);
  const displayMembers = members.slice(0, maxDisplay);
  const remainingCount = members.length - maxDisplay;

  const handleMemberAdded = () => {
    setShowAddMember(false);
    if (onMemberAdded) {
      onMemberAdded();
    }
  };

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between mb-3">
        <h5 className="text-md font-semibold text-foreground">
          Team Members ({members.length})
        </h5>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowAddMember(!showAddMember)}
        >
          <UserPlus className="w-4 h-4 mr-2" />
          Add Member
          {showAddMember ? (
            <ChevronUp className="w-4 h-4 ml-2" />
          ) : (
            <ChevronDown className="w-4 h-4 ml-2" />
          )}
        </Button>
      </div>

      {/* Add Member Section */}
      {showAddMember && projectId && (
        <div className="mb-4 p-4 border border-border rounded-lg bg-muted/30">
          <AddMembers
            projectId={projectId}
            existingMembers={members}
            onMemberAdded={handleMemberAdded}
          />
        </div>
      )}

      {/* Members List */}
      <div className="space-y-3">
        {members.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No members yet. Add the first member to get started!
          </div>
        ) : (
          <>
            {displayMembers.map((member) => (
              <div key={member.id} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-primary">
                      {member.name.charAt(0)}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {member.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {member.role}
                    </p>
                  </div>
                </div>
                <span className="text-xs text-muted-foreground">
                  Joined {new Date(member.joinedAt).toLocaleDateString()}
                </span>
              </div>
            ))}
            {remainingCount > 0 && (
              <p className="text-sm text-muted-foreground text-center">
                +{remainingCount} more members
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
