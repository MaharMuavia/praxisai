"use client";

import { ArrowRight, Menu, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Brand } from "./brand";
import { Button } from "./ui";

const links = [
  ["How it works", "/how-it-works"],
  ["For students", "/for-students"],
  ["For companies", "/for-companies"],
  ["Trust", "/trust"],
];

export function MarketingNav() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [open]);

  return (
    <header className="marketing-header">
      <Link className="marketing-skip-link" href="#main-content">
        Skip to content
      </Link>
      <div className="marketing-nav-inner">
        <Brand />
        <nav className="marketing-desktop-nav" aria-label="Primary navigation">
          {links.map(([label, href]) => (
            <Link key={href} href={href}>
              {label}
            </Link>
          ))}
          <Link href="/login">Log in</Link>
          <Button href="/contact" variant="primary">
            Submit a project <ArrowRight size={16} aria-hidden="true" />
          </Button>
        </nav>
        <button
          className="marketing-menu-button"
          type="button"
          aria-label={open ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={open}
          aria-controls="marketing-mobile-menu"
          onClick={() => setOpen((value) => !value)}
        >
          {open ? (
            <X size={22} aria-hidden="true" />
          ) : (
            <Menu size={22} aria-hidden="true" />
          )}
        </button>
      </div>
      {open ? (
        <nav
          id="marketing-mobile-menu"
          className="marketing-mobile-menu"
          aria-label="Mobile navigation"
        >
          {links.map(([label, href]) => (
            <Link key={href} href={href} onClick={() => setOpen(false)}>
              {label}
            </Link>
          ))}
          <Link href="/for-expert-leads" onClick={() => setOpen(false)}>
            For expert leads
          </Link>
          <Link href="/for-universities" onClick={() => setOpen(false)}>
            For universities
          </Link>
          <Link href="/trust" onClick={() => setOpen(false)}>
            Trust & safety
          </Link>
          <Link href="/login" onClick={() => setOpen(false)}>
            Log in
          </Link>
          <Button href="/contact" variant="primary">
            Submit a project <ArrowRight size={16} aria-hidden="true" />
          </Button>
          <Button href="/for-students" variant="secondary">
            Apply as a student
          </Button>
        </nav>
      ) : null}
    </header>
  );
}
