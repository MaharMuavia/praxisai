"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";

export type WorkspaceSearchItem = {
  label: string;
  href: string;
  detail: string;
  kind: "navigation" | "record";
};

export function WorkspaceCommandMenu({
  query,
  items,
  onClose,
}: {
  query: string;
  items: WorkspaceSearchItem[];
  onClose: () => void;
}) {
  const menuRef = useRef<HTMLDivElement>(null);
  const normalizedQuery = query.trim().toLocaleLowerCase();
  const matches = normalizedQuery
    ? items.filter((item) =>
        `${item.label} ${item.detail}`
          .toLocaleLowerCase()
          .includes(normalizedQuery),
      )
    : [];

  useEffect(() => {
    if (!normalizedQuery) return;
    const closeOnOutsideClick = (event: MouseEvent) => {
      if (
        event.target instanceof Node &&
        !menuRef.current?.contains(event.target)
      ) {
        onClose();
      }
    };
    document.addEventListener("mousedown", closeOnOutsideClick);
    return () => document.removeEventListener("mousedown", closeOnOutsideClick);
  }, [normalizedQuery, onClose]);

  if (!normalizedQuery) return null;

  return (
    <div
      ref={menuRef}
      className="workspace-command-menu"
      role="listbox"
      aria-label="Workspace search results"
    >
      <div className="workspace-command-scope">
        Loaded records and navigation
      </div>
      {matches.length === 0 ? (
        <div className="workspace-command-empty">
          No loaded workspace results match “{query}”.
        </div>
      ) : (
        matches.slice(0, 8).map((item) => (
          <Link
            href={item.href}
            key={`${item.kind}-${item.href}-${item.label}`}
            className="workspace-command-item"
            role="option"
            onClick={onClose}
          >
            <span>{item.label}</span>
            <small>{item.detail}</small>
          </Link>
        ))
      )}
    </div>
  );
}
