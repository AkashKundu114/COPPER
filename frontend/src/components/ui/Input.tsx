import React from "react";

type InputSize = "sm" | "md" | "lg";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  inputSize?: InputSize;
  label?: string;
  error?: string;
}

const sizeClasses: Record<InputSize, string> = {
  sm: "h-8 text-sm px-2.5",
  md: "h-9 text-base px-3",
  lg: "h-10 text-base px-3.5",
};

export function Input({ inputSize = "md", label, error, className = "", id, ...props }: InputProps) {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={inputId} className="text-xs text-text-secondary font-medium">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={[
          "bg-surface-base border border-border-subtle rounded-md",
          "text-text placeholder:text-text-tertiary",
          "focus:border-copper focus:ring-1 focus:ring-copper-glow",
          "transition-colors duration-100 outline-none",
          error ? "border-danger focus:border-danger focus:ring-danger/25" : "",
          sizeClasses[inputSize],
          className,
        ].filter(Boolean).join(" ")}
        {...props}
      />
      {error && <p className="text-2xs text-danger mt-0.5">{error}</p>}
    </div>
  );
}
