"use client";

import { Bell, CircleHelp, LogOut, Menu, Search, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState, type RefObject } from "react";
import { Brand } from "./brand";
import {
  WorkspaceCommandMenu,
  type WorkspaceSearchItem,
} from "./workspace-command-menu";
import { visibleNavigation, type WorkspaceRoot } from "./workspace-navigation";
import { demoEnvironment } from "../lib/demo-environment";

type SessionSummary = {
  display_name?: string | null;
  environment_label?: string | null;
  active_membership?: { organization_name?: string | null } | null;
  capabilities?: string[] | null;
};

type WorkspaceNotification = {
  id: string;
  title: string;
  body: string;
  read_at?: string | null;
  resource_path?: string | null;
};

export function WorkspaceSidebar({
  root,
  path,
  session,
  open,
  onClose,
  mobileTriggerRef,
}: {
  root: WorkspaceRoot;
  path: string;
  session: SessionSummary | null;
  open: boolean;
  onClose: () => void;
  mobileTriggerRef: RefObject<HTMLButtonElement | null>;
}) {
  const drawerRef = useRef<HTMLElement>(null);
  const environmentLabel =
    session?.environment_label?.toLowerCase() === "demo" &&
    !demoEnvironment.showEnvironmentBanner
      ? null
      : session?.environment_label;

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const focusable = drawerRef.current?.querySelector<HTMLElement>(
      "button, a, input, select, textarea, [tabindex]:not([tabindex='-1'])",
    );
    focusable?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        requestAnimationFrame(() => mobileTriggerRef.current?.focus());
        return;
      }
      if (event.key !== "Tab") return;
      const elements = Array.from(
        drawerRef.current?.querySelectorAll<HTMLElement>(
          "button, a, input, select, textarea, [tabindex]:not([tabindex='-1'])",
        ) ?? [],
      ).filter((element) => !element.hasAttribute("disabled"));
      if (elements.length === 0) return;
      const first = elements[0];
      const last = elements[elements.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [mobileTriggerRef, onClose, open]);

  const closeAndRestore = () => {
    onClose();
    requestAnimationFrame(() => mobileTriggerRef.current?.focus());
  };

  return (
    <>
      <aside
        ref={drawerRef}
        className={`sidebar ${open ? "open" : ""}`}
        aria-label={`${root} workspace navigation`}
      >
        <div className="sidebar-mobile-head">
          <Brand />
          <button
            aria-label="Close navigation"
            className="icon-button sidebar-close"
            onClick={closeAndRestore}
            type="button"
          >
            <X size={18} />
          </button>
        </div>
        <Brand />
        {session?.active_membership?.organization_name || environmentLabel ? (
          <div className="environment">
            {environmentLabel ? (
              <strong>{environmentLabel} environment</strong>
            ) : null}
            {environmentLabel &&
            session?.active_membership?.organization_name ? (
              <br />
            ) : null}
            {session?.active_membership?.organization_name}
          </div>
        ) : null}
        <div className="nav-group">Workspace</div>
        <nav aria-label={`${root} workspace navigation`}>
          {visibleNavigation(root, session).map(
            ({ label, href, icon: Icon, match }) => (
              <Link
                key={href + label}
                className={`nav-link ${match(path) ? "active" : ""}`}
                href={href}
                onClick={closeAndRestore}
              >
                <Icon size={17} /> {label}
              </Link>
            ),
          )}
        </nav>
        <div className="sidebar-foot">
          <Link className="nav-link" href="/trust" onClick={closeAndRestore}>
            <CircleHelp size={17} /> Help & escalation
          </Link>
        </div>
      </aside>
      {open ? (
        <button
          aria-label="Close navigation overlay"
          tabIndex={-1}
          className="sidebar-overlay"
          onClick={closeAndRestore}
          type="button"
        />
      ) : null}
    </>
  );
}

export function WorkspaceHeader({
  root,
  title,
  session,
  notifications,
  notificationOpen,
  globalSearch,
  onSearchChange,
  onToggleNotifications,
  onMarkRead,
  onOpenMobileNav,
  mobileTriggerRef,
  searchItems,
  onLogout,
  logoutBusy,
  logoutError,
}: {
  root: WorkspaceRoot;
  title: string;
  session: SessionSummary | null;
  notifications: WorkspaceNotification[] | null;
  notificationOpen: boolean;
  globalSearch: string;
  onSearchChange: (value: string) => void;
  onToggleNotifications: () => void;
  onMarkRead: (id: string) => void;
  onOpenMobileNav: () => void;
  mobileTriggerRef: RefObject<HTMLButtonElement | null>;
  searchItems: WorkspaceSearchItem[];
  onLogout: () => void;
  logoutBusy: boolean;
  logoutError: string | null;
}) {
  const notificationButton = useRef<HTMLButtonElement>(null);
  const [searchOpen, setSearchOpen] = useState(Boolean(globalSearch));
  useEffect(() => {
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape" && notificationOpen) {
        onToggleNotifications();
        notificationButton.current?.focus();
      }
    };
    document.addEventListener("keydown", close);
    return () => document.removeEventListener("keydown", close);
  }, [notificationOpen, onToggleNotifications]);
  const unread = notifications?.filter((item) => !item.read_at).length ?? 0;
  return (
    <header className="app-topbar">
      <div className="topbar-leading">
        <button
          aria-label="Open navigation"
          ref={mobileTriggerRef}
          className="icon-button mobile-menu-button"
          onClick={onOpenMobileNav}
          type="button"
        >
          <Menu size={19} />
        </button>
        <div className="breadcrumbs">
          PraxisAI <span>/</span> {root} <span>/</span> {title}
        </div>
      </div>
      <div className="topbar-actions">
        <div className="workspace-search-control">
          <label className="topbar-search">
            <Search size={15} aria-hidden="true" />
            <span className="sr-only">Search loaded workspace records</span>
            <input
              aria-label="Search loaded workspace records"
              onChange={(event) => {
                onSearchChange(event.target.value);
                setSearchOpen(true);
              }}
              onFocus={() => setSearchOpen(true)}
              placeholder="Search loaded records"
              value={globalSearch}
            />
          </label>
          {searchOpen ? (
            <WorkspaceCommandMenu
              query={globalSearch}
              items={searchItems}
              onClose={() => setSearchOpen(false)}
            />
          ) : null}
        </div>
        <div className="notification-control">
          <button
            ref={notificationButton}
            aria-expanded={notificationOpen}
            aria-label={`${unread} unread notifications`}
            className="icon-button"
            onClick={onToggleNotifications}
            type="button"
          >
            <Bell size={19} />
            {unread > 0 ? (
              <span className="notification-count">{unread}</span>
            ) : null}
          </button>
          {notificationOpen ? (
            <div
              className="notification-menu"
              role="region"
              aria-label="Notifications"
            >
              <strong>Notifications</strong>
              {notifications === null ? (
                <div className="notification-item">Loading…</div>
              ) : notifications.length === 0 ? (
                <div className="notification-item">No notifications.</div>
              ) : (
                notifications.slice(0, 8).map((item) => (
                  <Link
                    className={`notification-item ${item.read_at ? "" : "unread"}`}
                    href={item.resource_path ?? "#"}
                    key={item.id}
                    onClick={() => onMarkRead(item.id)}
                  >
                    <strong>{item.title}</strong>
                    <span>{item.body}</span>
                  </Link>
                ))
              )}
            </div>
          ) : null}
        </div>
        <span className="profile-chip">
          <span className="profile-avatar">
            {(session?.display_name ?? "S").slice(0, 1)}
          </span>
          <span className="profile-name">
            {session?.display_name ?? "Signed-in user"}
          </span>
        </span>
        <button
          className="logout-button"
          disabled={logoutBusy}
          onClick={onLogout}
          type="button"
          title={logoutBusy ? "Signing out" : "Sign out"}
        >
          <LogOut size={18} aria-hidden="true" />
          <span>{logoutBusy ? "Signing out…" : "Sign out"}</span>
        </button>
        {logoutError ? (
          <span className="sr-only" role="alert">
            {logoutError}
          </span>
        ) : null}
      </div>
    </header>
  );
}

export function WorkspacePageHeader({
  title,
  description,
  isDemoPreview,
}: {
  title: string;
  description: string;
  isDemoPreview: boolean;
}) {
  return (
    <div className="page-heading">
      <div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {isDemoPreview ? <span className="demo-badge">Demo preview</span> : null}
    </div>
  );
}
