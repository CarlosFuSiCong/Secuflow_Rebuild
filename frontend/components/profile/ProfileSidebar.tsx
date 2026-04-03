"use client";

import { useState } from "react";

const NAV_ITEMS = [
  { id: "basic-info", label: "Basic Information" },
  { id: "change-password", label: "Change Password" },
];

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
    <aside className="hidden md:block w-48 py-8 shrink-0">
      <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground mb-3 px-1">
        Sections
      </p>
      <ul className="space-y-0.5">
        {NAV_ITEMS.map((item) => (
          <li key={item.id}>
            <button
              onClick={() => scrollToSection(item.id)}
              className={`w-full text-left px-2 py-1.5 text-sm transition-colors ${
                activeSection === item.id
                  ? "text-foreground font-medium"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {item.label}
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
