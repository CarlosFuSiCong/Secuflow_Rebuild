"use client";

interface SectionHeaderProps {
  title: string;
  description: string;
}

export function SectionHeader({ title, description }: SectionHeaderProps) {
  return (
    <div className="col-span-8 lg:col-span-4">
      <h2 className="mb-1 text-lg font-semibold">{title}</h2>
      <p className="text-muted-foreground text-sm">{description}</p>
    </div>
  );
}