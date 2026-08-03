import { AppShell } from "../app-shell";

export function WorkspaceRoute({
  path,
  title,
  description,
}: {
  path: string;
  title: string;
  description: string;
}) {
  return <AppShell path={path} title={title} description={description} />;
}
