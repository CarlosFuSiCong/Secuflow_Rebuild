"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface FormFieldProps {
  id: string;
  label: string;
  type?: string;
  value?: string;
  placeholder?: string;
  readOnly?: boolean;
  disabled?: boolean;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export function FormField({
  id,
  label,
  type = "text",
  value,
  placeholder,
  readOnly = false,
  disabled = false,
  onChange,
}: FormFieldProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        type={type}
        value={value}
        placeholder={placeholder}
        readOnly={readOnly}
        disabled={disabled}
        onChange={onChange}
      />
    </div>
  );
}