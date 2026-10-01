import React from "react";

type BadgeVariant = "default" | "copper" | "success" | "warning" | "danger" | "info";

interface BadgeProps {
  variant?: BadgeVariant;
  className?: string;
  children: React.ReactNode;
}

const variantClasses: Record<BadgeVariant, string> = {
  default:  "bg-surface-elevated text-text-secondary border-border",
  copper:   "bg-copper-subtle text-copper border-copper/20",
  success:  "bg-success-dim text-success border-success/20",
  warning:  "bg-warning-dim text-warning border-warning/20",
  danger:   "bg-danger-dim text-danger border-danger/20",
  info:     "bg-info-dim text-info border-info/20",
};

export function Badge({ variant = "default", className = "", children }: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center h-5 px-1.5",
        "text-2xs font-medium font-mono rounded-sm border",
        variantClasses[variant],
        className,
      ].join(" ")}
    >
      {children}
    </span>
  );
}
