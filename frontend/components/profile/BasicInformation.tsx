"use client";

import { SectionHeader } from "./SectionHeader";
import { BasicInfoForm } from "./BasicInfoForm";

export function BasicInformation() {
  return (
    <section id="basic-info" className="pb-10 border-b border-border grid grid-cols-1 gap-8 lg:grid-cols-5">
      <div className="lg:col-span-2">
        <SectionHeader
          title="Basic Information"
          description="Manage your personal details and account information."
        />
      </div>
      <div className="lg:col-span-3">
        <BasicInfoForm />
      </div>
    </section>
  );
}
