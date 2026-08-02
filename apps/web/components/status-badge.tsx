export function ProjectStatusBadge({ status }: { status: string }) {
  return <span className="status-badge">{status.replaceAll("_", " ")}</span>;
}
