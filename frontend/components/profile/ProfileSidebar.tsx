"use client";

// Sidebar menu items
const SIDEBAR_ITEMS = {
  BASIC_INFO: "Basic Information",
  CHANGE_PASSWORD: "Change Password",
};

export function ProfileSidebar() {
  return (
    <aside className="border-border hidden w-64 border-r py-6 pr-6 md:block">
      <ul className="-ml-3 space-y-1">
        <li className="bg-accent-foreground/5 text-accent-foreground hover:bg-accent-foreground/10 cursor-pointer rounded-md px-3 py-2 text-sm font-medium">
          <a>{SIDEBAR_ITEMS.BASIC_INFO}</a>
        </li>
        <li className="text-muted-foreground hover:bg-accent-foreground/10 cursor-pointer rounded-md px-3 py-2 text-sm font-medium">
          <a>{SIDEBAR_ITEMS.CHANGE_PASSWORD}</a>
        </li>
      </ul>
    </aside>
  );
}