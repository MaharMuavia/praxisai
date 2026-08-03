import type { ReactNode } from "react";

export function DemoBadge({
  children = "Demo data",
}: {
  children?: ReactNode;
}) {
  return <span className="demo-boundary-badge">{children}</span>;
}

export function DemoNotice({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`demo-boundary-notice ${className}`.trim()} role="note">
      <DemoBadge />
      <span>{children}</span>
    </div>
  );
}
