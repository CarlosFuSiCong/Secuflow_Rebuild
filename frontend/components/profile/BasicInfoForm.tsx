"use client";

import { useState, useEffect } from "react";
import { fetchCurrentUser, updateProfile } from "@/lib/api/users";
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
  MESSAGE_NO_CHANGES: "No changes detected",
};

export function BasicInfoForm() {
  const [user, setUser] = useState<User | null>(null);
  const [loadingUser, setLoadingUser] = useState<boolean>(false);
  const [firstName, setFirstName] = useState<string>("");
  const [lastName, setLastName] = useState<string>("");
  const [contactEmail, setContactEmail] = useState<string>("");

  // Store original values for comparison
  const [originalFirstName, setOriginalFirstName] = useState<string>("");
  const [originalLastName, setOriginalLastName] = useState<string>("");
  const [originalContactEmail, setOriginalContactEmail] = useState<string>("");

  const { loading, error, message, handleSubmit } = useProfileForm({
    apiCall: updateProfile,
    onSuccess: async () => {
      // Refresh user data
      const me = await fetchCurrentUser();
      if (me.succeed && me.data) {
        setUser(me.data);
        const newFirstName = me.data.first_name || "";
        const newLastName = me.data.last_name || "";
        const newContactEmail = me.data.contact_email || "";

        setFirstName(newFirstName);
        setLastName(newLastName);
        setContactEmail(newContactEmail);

        // Update original values
        setOriginalFirstName(newFirstName);
        setOriginalLastName(newLastName);
        setOriginalContactEmail(newContactEmail);
      }
    },
    successMessage: TEXT.MESSAGE_SUCCESS,
  });

  useEffect(() => {
    const load = async () => {
      setLoadingUser(true);
      try {
        const resp = await fetchCurrentUser();
        if (resp.succeed && resp.data) {
          setUser(resp.data);
          const loadedFirstName = resp.data.first_name || "";
          const loadedLastName = resp.data.last_name || "";
          const loadedContactEmail = resp.data.contact_email || "";

          setFirstName(loadedFirstName);
          setLastName(loadedLastName);
          setContactEmail(loadedContactEmail);

          // Store original values
          setOriginalFirstName(loadedFirstName);
          setOriginalLastName(loadedLastName);
          setOriginalContactEmail(loadedContactEmail);
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
    // Check if data has changed
    if (
      firstName === originalFirstName &&
      lastName === originalLastName &&
      contactEmail === originalContactEmail
    ) {
      alert(TEXT.MESSAGE_NO_CHANGES);
      return;
    }

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