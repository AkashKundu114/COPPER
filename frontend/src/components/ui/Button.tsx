import React from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "icon";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: React.ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-copper text-text-inverse hover:bg-copper-bright font-medium " +
    "shadow-sm hover:shadow-md active:scale-[0.98]",
  secondary:
    "bg-surface-elevated text-text border border-border-subtle " +
    "hover:bg-surface-hover hover:border-border-highlight",
  ghost:
    "bg-transparent text-text-secondary hover:bg-surface-hover hover:text-text",
  danger:
    "bg-danger-dim text-danger border border-danger/20 " +
    "hover:bg-danger/20 hover:border-danger/30",
  icon:
    "bg-transparent text-text-secondary hover:bg-surface-hover " +
    "hover:text-text p-1.5 !rounded-md",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-7 px-2.5 text-xs gap-1",
  md: "h-8 px-3 text-sm gap-1.5",
  lg: "h-9 px-4 text-base gap-2",
};

export function Button({
  variant = "secondary",
  size = "md",
  className = "",
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={[
        "inline-flex items-center justify-center rounded-md",
        "transition-all duration-100 cursor-pointer",
        "disabled:opacity-40 disabled:pointer-events-none",
        "select-none whitespace-nowrap",
        variantClasses[variant],
        variant !== "icon" ? sizeClasses[size] : "",
        className,
      ].filter(Boolean).join(" ")}
      {...props}
    >
      {children}
    </button>
  );
}
