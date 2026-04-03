"use client";

import { Logo } from "@/components/common/Logo";

type AuthHeaderProps = {
  title: string;
  description?: string;
  showLogoOnMobile?: boolean;
};

export function AuthHeader({ title, description, showLogoOnMobile = true }: AuthHeaderProps) {
  return (
    <div className="mb-6 space-y-4">
      {showLogoOnMobile && <Logo className="block h-9 w-9 md:hidden" />}
      <div className="flex flex-col gap-y-2">
        {description ? (
          <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground">
            {description}
          </p>
        ) : null}
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      </div>
    </div>
  );
}
