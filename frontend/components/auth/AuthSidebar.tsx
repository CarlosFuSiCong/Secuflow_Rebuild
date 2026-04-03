"use client";

import { cn } from "@/lib/utils";

const FEATURES = [
  "Contributor trust network mapping",
  "STC & MC-STC risk scoring",
  "Branch-level security insights",
  "Automated vulnerability analysis",
];

type AuthSidebarProps = {
  className?: string;
};

export function AuthSidebar({ className }: AuthSidebarProps) {
  return (
    <div
      className={cn(
        "hidden md:flex md:w-[40%] min-h-full flex-col justify-between p-12 bg-foreground text-background",
        className
      )}
    >
      {/* Top: wordmark */}
      <div>
        <span className="text-sm font-semibold tracking-widest uppercase opacity-90">
          Secuflow
        </span>
      </div>

      {/* Middle: tagline + feature list */}
      <div className="space-y-10">
        <h2 className="text-4xl font-light leading-[1.15] tracking-tight">
          Security,
          <br />
          made legible.
        </h2>
        <ul className="space-y-3">
          {FEATURES.map((feature) => (
            <li key={feature} className="flex items-start gap-3 text-sm opacity-70">
              <span className="mt-px select-none opacity-50">—</span>
              <span>{feature}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Bottom: copyright */}
      <p className="text-xs opacity-30 tracking-wide">
        © {new Date().getFullYear()} Secuflow. All rights reserved.
      </p>
    </div>
  );
}
