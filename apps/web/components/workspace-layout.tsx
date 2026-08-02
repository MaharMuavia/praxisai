"use client";

import { Bell, CircleHelp, LogOut, Menu, Search, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef } from "react";
import { Brand } from "./brand";
import { navigation, type WorkspaceRoot } from "./workspace-navigation";

type SessionSummary = {
  display_name?: string | null;
  environment_label?: string | null;
  active_membership?: { organization_name?: string | null } | null;
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
}: {
  root: WorkspaceRoot;
  path: string;
  session: SessionSummary | null;
  open: boolean;
  onClose: () => void;
}) {
  return (
    <>
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="sidebar-mobile-head">
          <Brand />
          <button
            aria-label="Close navigation"
            className="icon-button sidebar-close"
            onClick={onClose}
            type="button"
          >
            <X size={18} />
          </button>
        </div>
        <Brand />
        <div className="environment">
          <strong>{session?.environment_label ?? "Demo"} environment</strong>
          <br />
          {session?.active_membership?.organization_name ?? "PraxisAI pilot"}
        </div>
        <div className="nav-group">Workspace</div>
        <nav aria-label={`${root} workspace navigation`}>
          {navigation[root].map(([label, href, Icon]) => (
            <Link
              key={href + label}
              className={`nav-link ${path === href ? "active" : ""}`}
              href={href}
              onClick={onClose}
            >
              <Icon size={17} /> {label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-foot">
          <Link className="nav-link" href="/trust">
            <CircleHelp size={17} /> Help & escalation
          </Link>
        </div>
      </aside>
      {open ? (
        <button
          aria-label="Close navigation overlay"
          className="sidebar-overlay"
          onClick={onClose}
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
}) {
  const notificationButton = useRef<HTMLButtonElement>(null);
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
        <label className="topbar-search">
          <Search size={15} aria-hidden="true" />
          <span className="sr-only">Search workspace</span>
          <input
            aria-label="Search workspace"
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search workspace"
            value={globalSearch}
          />
        </label>
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
        <LogOut className="logout-icon" size={18} aria-hidden="true" />
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
      <span className="demo-badge">
        {isDemoPreview ? "Demo preview" : "Demo data"}
      </span>
    </div>
  );
}
