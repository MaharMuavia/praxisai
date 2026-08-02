import { fireEvent, render, screen } from "@testing-library/react";
import { createRef } from "react";
import { describe, expect, it, vi } from "vitest";
import { WorkspaceCommandMenu } from "./workspace-command-menu";
import {
  WorkspaceHeader,
  WorkspacePageHeader,
  WorkspaceSidebar,
} from "./workspace-layout";

describe("workspace shell primitives", () => {
  it("does not render a fictional badge for real data", () => {
    const { rerender } = render(
      <WorkspacePageHeader
        title="Projects"
        description="Authorized projects"
        isDemoPreview={false}
      />,
    );
    expect(screen.queryByText("Demo data")).not.toBeInTheDocument();
    expect(screen.queryByText("Demo preview")).not.toBeInTheDocument();

    rerender(
      <WorkspacePageHeader
        title="Projects"
        description="Preview projects"
        isDemoPreview
      />,
    );
    expect(screen.getByText("Demo preview")).toBeInTheDocument();
  });

  it("keeps nested workspace routes active", () => {
    render(
      <WorkspaceSidebar
        root="client"
        path="/client/projects/33333333-3333-4333-8333-333333333333"
        session={null}
        open={false}
        onClose={vi.fn()}
        mobileTriggerRef={createRef<HTMLButtonElement>()}
      />,
    );
    expect(screen.getByRole("link", { name: /Projects/ })).toHaveClass(
      "active",
    );
    expect(screen.getByRole("link", { name: /Overview/ })).not.toHaveClass(
      "active",
    );
  });

  it("searches only the loaded scope and exposes real navigation actions", () => {
    render(
      <WorkspaceCommandMenu
        query="directory"
        items={[
          {
            label: "Northstar directory",
            href: "/client/projects/1",
            detail: "loaded project record",
            kind: "record",
          },
        ]}
        onClose={vi.fn()}
      />,
    );
    expect(
      screen.getByText("Loaded records and navigation"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /Northstar directory/ }),
    ).toHaveAttribute("href", "/client/projects/1");
  });

  it("uses an accessible logout button and pending state", () => {
    const onLogout = vi.fn();
    const trigger = createRef<HTMLButtonElement>();
    const { rerender } = render(
      <WorkspaceHeader
        root="client"
        title="Overview"
        session={null}
        notifications={[]}
        notificationOpen={false}
        globalSearch=""
        onSearchChange={vi.fn()}
        onToggleNotifications={vi.fn()}
        onMarkRead={vi.fn()}
        onOpenMobileNav={vi.fn()}
        mobileTriggerRef={trigger}
        searchItems={[]}
        onLogout={onLogout}
        logoutBusy={false}
        logoutError={null}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /sign out/i }));
    expect(onLogout).toHaveBeenCalledOnce();
    rerender(
      <WorkspaceHeader
        root="client"
        title="Overview"
        session={null}
        notifications={[]}
        notificationOpen={false}
        globalSearch=""
        onSearchChange={vi.fn()}
        onToggleNotifications={vi.fn()}
        onMarkRead={vi.fn()}
        onOpenMobileNav={vi.fn()}
        mobileTriggerRef={trigger}
        searchItems={[]}
        onLogout={onLogout}
        logoutBusy
        logoutError={null}
      />,
    );
    expect(screen.getByRole("button", { name: /signing out/i })).toBeDisabled();
  });
});
