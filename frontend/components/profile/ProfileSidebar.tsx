"use client";

import { useState } from "react";

// Sidebar menu items
const SIDEBAR_ITEMS = {
  BASIC_INFO: "Basic Information",
  CHANGE_PASSWORD: "Change Password",
};

export function ProfileSidebar() {
  const [activeSection, setActiveSection] = useState<string>("basic-info");

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
      setActiveSection(sectionId);
    }
  };

  return (
    <aside className="border-border hidden w-64 border-r py-6 pr-6 md:block">
      <ul className="-ml-3 space-y-1">
        <li
          className={`cursor-pointer rounded-md px-3 py-2 text-sm font-medium ${
            activeSection === "basic-info"
              ? "bg-accent-foreground/5 text-accent-foreground"
              : "text-muted-foreground hover:bg-accent-foreground/10"
          }`}
          onClick={() => scrollToSection("basic-info")}
        >
          <a>{SIDEBAR_ITEMS.BASIC_INFO}</a>
        </li>
        <li
          className={`cursor-pointer rounded-md px-3 py-2 text-sm font-medium ${
            activeSection === "change-password"
              ? "bg-accent-foreground/5 text-accent-foreground"
              : "text-muted-foreground hover:bg-accent-foreground/10"
          }`}
          onClick={() => scrollToSection("change-password")}
        >
          <a>{SIDEBAR_ITEMS.CHANGE_PASSWORD}</a>
        </li>
      </ul>
    </aside>
  );
}