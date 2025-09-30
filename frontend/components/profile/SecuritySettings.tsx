"use client";

import { useState } from "react";
import { changePassword } from "@/lib/api/users";
import { SectionHeader } from "./SectionHeader";
import { FormField } from "./FormField";
import { FormContainer } from "./FormContainer";
import { useProfileForm } from "@/lib/hooks/useProfileForm";

// Text constants
const TEXT = {
  SECTION_TITLE: "Change Password",
  SECTION_DESCRIPTION: "Update your password and security preferences.",
  LABEL_NEW_PASSWORD: "New password",
  LABEL_CONFIRM_PASSWORD: "Confirm password",
  BUTTON_SAVE: "Change Password",
  BUTTON_SAVING: "Changing...",
  MESSAGE_SUCCESS: "Password changed successfully",
  ERROR_PASSWORD_MISMATCH: "Passwords do not match",
};

export function SecuritySettings() {
  const [newPassword, setNewPassword] = useState<string>("");
  const [confirmPassword, setConfirmPassword] = useState<string>("");

  const { loading, error, message, handleSubmit } = useProfileForm({
    apiCall: ({ oldPassword, newPassword, newPasswordConfirm }: {
      oldPassword: string;
      newPassword: string;
      newPasswordConfirm: string;
    }) => changePassword(oldPassword, newPassword, newPasswordConfirm),
    onSuccess: () => {
      // Clear form on success
      setNewPassword("");
      setConfirmPassword("");
    },
    successMessage: TEXT.MESSAGE_SUCCESS,
  });

  const onSubmit = () => {
    if (newPassword !== confirmPassword) {
      alert(TEXT.ERROR_PASSWORD_MISMATCH);
      return;
    }
    handleSubmit({
      oldPassword: "",
      newPassword: newPassword,
      newPasswordConfirm: confirmPassword,
    });
  };

  return (
    <section className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-8">
      <SectionHeader
        title={TEXT.SECTION_TITLE}
        description={TEXT.SECTION_DESCRIPTION}
      />
      <FormContainer
        onSubmit={onSubmit}
        loading={loading}
        error={error}
        message={message}
        submitText={TEXT.BUTTON_SAVE}
        loadingText={TEXT.BUTTON_SAVING}
      >
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
    </section>
  );
}