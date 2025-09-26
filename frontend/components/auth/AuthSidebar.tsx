"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

type AuthSidebarProps = {
  className?: string;
  theme?: "light" | "dark" | "inverse";
};

export function AuthSidebar({ className, theme = "inverse" }: AuthSidebarProps) {
  const themeClasses =
    theme === "inverse"
      ? "bg-background text-foreground dark:bg-foreground dark:text-background"
      : theme === "dark"
        ? "bg-foreground text-background"
        : "bg-background text-foreground";

  return (
    <div className={cn("hidden min-h-full w-[40%] flex-col-reverse p-12 md:flex", themeClasses, className)}>
      <div className="flex h-full flex-col justify-between gap-y-12">
        <div className="max-w-xl">
          <Avatar className="mb-6 h-12 w-12">
            <AvatarImage src="https://github.com/shadcn.png" alt="@shadcn" />
            <AvatarFallback>ST</AvatarFallback>
          </Avatar>
          <p className="mb-6 text-lg opacity-90">
            "Secuflow has revolutionized our security workflow. The automated vulnerability
            scanning and comprehensive reporting give us confidence in our code quality.
            It's an essential tool for any development team serious about security."
          </p>
        </div>
        <div>
          <p className="font-semibold">Sicong Fu</p>
          <p className="opacity-80">Security Engineer at TechCorp</p>
        </div>
      </div>
    </div>
  );
}


