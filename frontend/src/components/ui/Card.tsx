import React from "react";

type CardVariant = "default" | "glass" | "featured" | "flush";

interface CardProps {
  variant?: CardVariant;
  className?: string;
  children: React.ReactNode;
  onClick?: () => void;
}

const variantClasses: Record<CardVariant, string> = {
  default:  "surface-card p-4",
  glass:    "surface-glass rounded-xl p-4",
  featured: "surface-card glow-copper border-copper/30 p-4",
  flush:    "surface-card p-0 overflow-hidden",
};

export function Card({ variant = "default", className = "", children, onClick }: CardProps) {
  return (
    <div
      className={`rounded-xl ${variantClasses[variant]} ${className}`}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return <div className={`mb-3 ${className}`}>{children}</div>;
}

export function CardTitle({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return <h3 className={`text-md font-semibold text-text ${className}`}>{children}</h3>;
}

export function CardDescription({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return <p className={`text-sm text-text-secondary mt-0.5 ${className}`}>{children}</p>;
}

export function CardContent({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return <div className={className}>{children}</div>;
}

export function CardFooter({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return <div className={`mt-4 flex items-center gap-2 ${className}`}>{children}</div>;
}
