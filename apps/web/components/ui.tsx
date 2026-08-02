import Link from "next/link";
import type { ReactNode } from "react";

type ButtonVariant =
  | "primary"
  | "secondary"
  | "outline"
  | "ghost"
  | "destructive"
  | "light"
  | "outline-light"
  | "link";

type ButtonProps = {
  children: ReactNode;
  variant?: ButtonVariant;
  href?: string;
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
  ariaLabel?: string;
  onClick?: () => void;
};

export function Button({
  children,
  variant = "primary",
  href,
  type = "button",
  disabled = false,
  ariaLabel,
  onClick,
}: ButtonProps) {
  const className = `ui-button ui-button-${variant}`;
  if (href) {
    return (
      <Link className={className} href={href} aria-label={ariaLabel}>
        {children}
      </Link>
    );
  }
  return (
    <button
      className={className}
      type={type}
      disabled={disabled}
      aria-label={ariaLabel}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`ui-card ${className}`.trim()}>{children}</div>;
}

export function StatusBadge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning" | "ai";
}) {
  return <span className={`ui-status ui-status-${tone}`}>{children}</span>;
}

export function SectionHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="marketing-section-header">
      <p className="marketing-eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      {description ? (
        <p className="marketing-section-description">{description}</p>
      ) : null}
    </div>
  );
}
