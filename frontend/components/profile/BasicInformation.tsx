"use client";

import { SectionHeader } from "./SectionHeader";
import { BasicInfoForm } from "./BasicInfoForm";

// Text constants
const TEXT = {
  SECTION_TITLE: "Basic Information",
  SECTION_DESCRIPTION: "Manage your personal details and account information.",
};

export function BasicInformation() {
  return (
    <section id="basic-info" className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-8">
      <SectionHeader
        title={TEXT.SECTION_TITLE}
        description={TEXT.SECTION_DESCRIPTION}
      />
      <BasicInfoForm />
    </section>
  );
}