"use client";

import { useState, useEffect } from "react";
import { getCurrentUser, updateProfile } from "@/lib/api/users";
import type { User } from "@/lib/types/user";
import { FormField } from "./FormField";
import { FormContainer } from "./FormContainer";
import { useProfileForm } from "@/lib/hooks/useProfileForm";

// Text constants
const TEXT = {
  LABEL_USERNAME: "Username",
  LABEL_FIRST_NAME: "First name",
  LABEL_LAST_NAME: "Last name",
  LABEL_CONTACT_EMAIL: "Contact email",
  BUTTON_SAVE: "Save",
  BUTTON_SAVING: "Saving...",
  MESSAGE_SUCCESS: "Profile updated",
  MESSAGE_ERROR_LOAD: "Failed to load user",
};

export function BasicInfoForm() {
  const [user, setUser] = useState<User | null>(null);
  const [loadingUser, setLoadingUser] = useState<boolean>(false);
  const [firstName, setFirstName] = useState<string>("");
  const [lastName, setLastName] = useState<string>("");
  const [contactEmail, setContactEmail] = useState<string>("");

  const { loading, error, message, handleSubmit } = useProfileForm({
    apiCall: updateProfile,
    onSuccess: async () => {
      // Refresh user data
      const me = await getCurrentUser();
      if (me.succeed && me.data) {
        setUser(me.data);
        setFirstName(me.data.first_name || "");
        setLastName(me.data.last_name || "");
        setContactEmail(me.data.contact_email || "");
      }
    },
    successMessage: TEXT.MESSAGE_SUCCESS,
  });

  useEffect(() => {
    const load = async () => {
      setLoadingUser(true);
      try {
        const resp = await getCurrentUser();
        if (resp.succeed && resp.data) {
          setUser(resp.data);
          setFirstName(resp.data.first_name || "");
          setLastName(resp.data.last_name || "");
          setContactEmail(resp.data.contact_email || "");
        }
      } catch (e: any) {
        console.error(TEXT.MESSAGE_ERROR_LOAD, e);
      } finally {
        setLoadingUser(false);
      }
    };
    load();
  }, []);

  const onSubmit = () => {
    handleSubmit({
      contact_email: contactEmail,
      first_name: firstName,
      last_name: lastName,
    });
  };

  return (
    <FormContainer
      onSubmit={onSubmit}
      loading={loading}
      error={error}
      message={message}
      submitText={TEXT.BUTTON_SAVE}
      loadingText={TEXT.BUTTON_SAVING}
    >
      <FormField
        id="username"
        label={TEXT.LABEL_USERNAME}
        value={user?.username || ""}
        readOnly
      />
      <FormField
        id="firstname"
        label={TEXT.LABEL_FIRST_NAME}
        value={firstName}
        onChange={(e) => setFirstName(e.target.value)}
        disabled={loadingUser}
      />
      <FormField
        id="lastname"
        label={TEXT.LABEL_LAST_NAME}
        value={lastName}
        onChange={(e) => setLastName(e.target.value)}
        disabled={loadingUser}
      />
      <FormField
        id="contact_email"
        label={TEXT.LABEL_CONTACT_EMAIL}
        type="email"
        value={contactEmail}
        onChange={(e) => setContactEmail(e.target.value)}
        disabled={loadingUser}
      />
    </FormContainer>
  );
}