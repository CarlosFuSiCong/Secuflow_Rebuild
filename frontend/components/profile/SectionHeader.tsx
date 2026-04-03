"use client";

interface SectionHeaderProps {
  title: string;
  description: string;
}

export function SectionHeader({ title, description }: SectionHeaderProps) {
  return (
    <div>
      <h2 className="text-base font-semibold tracking-tight mb-1">{title}</h2>
      <p className="text-xs text-muted-foreground">{description}</p>
    </div>
  );
}
