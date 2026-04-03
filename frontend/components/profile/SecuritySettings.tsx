"use client";

import { useState } from "react";
import { changePassword } from "@/lib/api/users";
import { SectionHeader } from "./SectionHeader";
import { FormField } from "./FormField";
import { FormContainer } from "./FormContainer";
import { useProfileForm } from "@/lib/hooks/useProfileForm";
import { toast } from "sonner";

const TEXT = {
  SECTION_TITLE: "Change Password",
  SECTION_DESCRIPTION: "Update your password and security preferences.",
  LABEL_CURRENT_PASSWORD: "Current password",
  LABEL_NEW_PASSWORD: "New password",
  LABEL_CONFIRM_PASSWORD: "Confirm password",
  BUTTON_SAVE: "Change Password",
  BUTTON_SAVING: "Changing...",
  MESSAGE_SUCCESS: "Password changed successfully",
  ERROR_PASSWORD_MISMATCH: "Passwords do not match",
  ERROR_EMPTY_CURRENT_PASSWORD: "Please enter your current password",
};

export function SecuritySettings() {
  const [currentPassword, setCurrentPassword] = useState<string>("");
  const [newPassword, setNewPassword] = useState<string>("");
  const [confirmPassword, setConfirmPassword] = useState<string>("");

  const { loading, handleSubmit } = useProfileForm({
    apiCall: ({ oldPassword, newPassword, newPasswordConfirm }: {
      oldPassword: string;
      newPassword: string;
      newPasswordConfirm: string;
    }) => changePassword(oldPassword, newPassword, newPasswordConfirm),
    onSuccess: () => {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    },
    successMessage: TEXT.MESSAGE_SUCCESS,
  });

  const onSubmit = () => {
    if (!currentPassword.trim()) {
      toast.error(TEXT.ERROR_EMPTY_CURRENT_PASSWORD);
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error(TEXT.ERROR_PASSWORD_MISMATCH);
      return;
    }

    handleSubmit({
      oldPassword: currentPassword,
      newPassword: newPassword,
      newPasswordConfirm: confirmPassword,
    });
  };

  return (
    <section id="change-password" className="grid grid-cols-1 gap-8 lg:grid-cols-5">
      <div className="lg:col-span-2">
        <SectionHeader
          title={TEXT.SECTION_TITLE}
          description={TEXT.SECTION_DESCRIPTION}
        />
      </div>
      <div className="lg:col-span-3">
        <FormContainer
          onSubmit={onSubmit}
          loading={loading}
          submitText={TEXT.BUTTON_SAVE}
          loadingText={TEXT.BUTTON_SAVING}
        >
          <FormField
            id="current-password"
            label={TEXT.LABEL_CURRENT_PASSWORD}
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            disabled={loading}
          />
          <FormField
            id="new-password"
            label={TEXT.LABEL_NEW_PASSWORD}
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            disabled={loading}
          />
          <FormField
            id="confirm-password"
            label={TEXT.LABEL_CONFIRM_PASSWORD}
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            disabled={loading}
          />
        </FormContainer>
      </div>
    </section>
  );
}
