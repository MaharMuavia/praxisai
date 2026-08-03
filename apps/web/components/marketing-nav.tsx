"use client";

import { ArrowRight, ChevronDown, Menu, X } from "lucide-react";
import Link from "next/link";
import {
  useEffect,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react";
import { Brand } from "./brand";
import { ScrollProgress } from "./motion";
import { Button } from "./ui";

type MenuItem = { label: string; href: string; detail?: string };
type MenuConfig = { label: string; items: MenuItem[] };

const menus: MenuConfig[] = [
  {
    label: "Product",
    items: [
      {
        label: "How it works",
        href: "/how-it-works",
        detail: "From brief to verified proof",
      },
      {
        label: "Project delivery",
        href: "/how-it-works/clients",
        detail: "A managed path to release",
      },
      {
        label: "Practical learning",
        href: "/for-students",
        detail: "Practice before paid work",
      },
      {
        label: "Verified credentials",
        href: "/trust",
        detail: "Evidence people can inspect",
      },
    ],
  },
  {
    label: "Solutions",
    items: [
      { label: "AI workflow automation", href: "/solutions/ai-automation" },
      { label: "Data dashboards", href: "/solutions/data-dashboards" },
      { label: "Internal tools", href: "/solutions/internal-tools" },
      {
        label: "Customer & operations portals",
        href: "/solutions/customer-portals",
      },
    ],
  },
  {
    label: "Company",
    items: [
      { label: "About", href: "/about" },
      { label: "Impact", href: "/impact" },
      { label: "Expert leads", href: "/for-expert-leads" },
      { label: "Universities", href: "/for-universities" },
      { label: "Contact", href: "/contact" },
    ],
  },
];

const audienceLinks: MenuItem[] = [
  { label: "For students", href: "/for-students" },
  { label: "For companies", href: "/for-companies" },
];

export function MarketingNav() {
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const triggerRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const dropdownRefs = useRef<Record<string, HTMLAnchorElement[]>>({});
  const mobileTriggerRef = useRef<HTMLButtonElement>(null);
  const mobileRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    const onPointerDown = (event: PointerEvent) => {
      if (!(event.target instanceof Element)) return;
      if (!event.target.closest(".marketing-nav-menu")) setOpenMenu(null);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        if (mobileOpen) {
          setMobileOpen(false);
          requestAnimationFrame(() => mobileTriggerRef.current?.focus());
        }
        if (openMenu) {
          const trigger = triggerRefs.current[openMenu];
          setOpenMenu(null);
          requestAnimationFrame(() => trigger?.focus());
        }
      }
      if (mobileOpen && event.key === "Tab") {
        const focusable = Array.from(
          mobileRef.current?.querySelectorAll<HTMLElement>(
            "a, button, input, select, textarea, [tabindex]:not([tabindex='-1'])",
          ) ?? [],
        );
        if (focusable.length > 0) {
          const first = focusable[0];
          const last = focusable[focusable.length - 1];
          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
          }
        }
      }
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("scroll", onScroll);
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [mobileOpen, openMenu]);

  useEffect(() => {
    if (!mobileOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const firstLink =
      mobileRef.current?.querySelector<HTMLElement>("a, button");
    firstLink?.focus();
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [mobileOpen]);

  const closeMobile = () => {
    setMobileOpen(false);
    requestAnimationFrame(() => mobileTriggerRef.current?.focus());
  };
  const closeMenu = (label: string) => {
    setOpenMenu(null);
    requestAnimationFrame(() => triggerRefs.current[label]?.focus());
  };

  const openDisclosure = (label: string) => {
    setOpenMenu(label);
    requestAnimationFrame(() => dropdownRefs.current[label]?.[0]?.focus());
  };

  const moveWithinMenu = (
    event: ReactKeyboardEvent<HTMLAnchorElement>,
    label: string,
    index: number,
  ) => {
    const links = dropdownRefs.current[label] ?? [];
    if (event.key === "Escape") {
      event.preventDefault();
      closeMenu(label);
      return;
    }
    if (event.key === "Tab") {
      setOpenMenu(null);
      return;
    }
    const nextIndex =
      event.key === "ArrowDown"
        ? (index + 1) % links.length
        : event.key === "ArrowUp"
          ? (index - 1 + links.length) % links.length
          : event.key === "Home"
            ? 0
            : event.key === "End"
              ? links.length - 1
              : null;
    if (nextIndex === null) return;
    event.preventDefault();
    links[nextIndex]?.focus();
  };

  return (
    <header className={`marketing-header ${scrolled ? "is-scrolled" : ""}`}>
      <ScrollProgress />
      <Link className="marketing-skip-link" href="#main-content">
        Skip to content
      </Link>
      <div className="marketing-nav-inner">
        <Brand />
        <nav className="marketing-desktop-nav" aria-label="Primary navigation">
          {menus.map((menu) => {
            const isOpen = openMenu === menu.label;
            return (
              <div className="marketing-nav-menu" key={menu.label}>
                <button
                  aria-expanded={isOpen}
                  aria-haspopup="menu"
                  className="marketing-nav-trigger"
                  ref={(node) => {
                    triggerRefs.current[menu.label] = node;
                  }}
                  type="button"
                  aria-controls={`marketing-menu-${menu.label.toLowerCase()}`}
                  onClick={() =>
                    isOpen ? setOpenMenu(null) : openDisclosure(menu.label)
                  }
                  onKeyDown={(event) => {
                    if (
                      event.key === "ArrowDown" ||
                      event.key === "Enter" ||
                      event.key === " "
                    ) {
                      event.preventDefault();
                      openDisclosure(menu.label);
                    }
                  }}
                >
                  {menu.label} <ChevronDown size={14} aria-hidden="true" />
                </button>
                {isOpen ? (
                  <div
                    className="marketing-dropdown"
                    id={`marketing-menu-${menu.label.toLowerCase()}`}
                    role="menu"
                    onBlur={(event) => {
                      if (!event.currentTarget.contains(event.relatedTarget)) {
                        setOpenMenu(null);
                      }
                    }}
                  >
                    {menu.items.map((item, index) => (
                      <Link
                        href={item.href}
                        key={item.href}
                        role="menuitem"
                        ref={(node) => {
                          const links = dropdownRefs.current[menu.label] ?? [];
                          if (node) links[index] = node;
                          dropdownRefs.current[menu.label] = links;
                        }}
                        onKeyDown={(event) =>
                          moveWithinMenu(event, menu.label, index)
                        }
                        onClick={() => closeMenu(menu.label)}
                      >
                        <span>{item.label}</span>
                        {item.detail ? <small>{item.detail}</small> : null}
                      </Link>
                    ))}
                  </div>
                ) : null}
              </div>
            );
          })}
          {audienceLinks.map((item) => (
            <Link
              className="marketing-audience-link"
              href={item.href}
              key={item.href}
            >
              {item.label}
            </Link>
          ))}
          <Link className="marketing-judge-link" href="/judge">
            Judge walkthrough
          </Link>
          <Link className="marketing-login-link" href="/login">
            Log in
          </Link>
          <Button href="/contact" variant="primary">
            Submit a project <ArrowRight size={16} aria-hidden="true" />
          </Button>
        </nav>
        <button
          ref={mobileTriggerRef}
          className="marketing-menu-button"
          type="button"
          aria-label={
            mobileOpen ? "Close navigation menu" : "Open navigation menu"
          }
          aria-expanded={mobileOpen}
          aria-controls="marketing-mobile-menu"
          onClick={() => setMobileOpen((value) => !value)}
        >
          {mobileOpen ? (
            <X size={22} aria-hidden="true" />
          ) : (
            <Menu size={22} aria-hidden="true" />
          )}
        </button>
      </div>
      {mobileOpen ? (
        <>
          <button
            className="marketing-mobile-backdrop"
            aria-label="Close navigation overlay"
            type="button"
            onClick={closeMobile}
          />
          <nav
            id="marketing-mobile-menu"
            ref={mobileRef}
            className="marketing-mobile-menu"
            aria-label="Mobile navigation"
          >
            <div className="mobile-menu-intro">
              <span>PraxisAI</span>
              <small>The AI-operated apprenticeship studio</small>
            </div>
            {menus.map((menu) => (
              <div className="mobile-menu-group" key={menu.label}>
                <span>{menu.label}</span>
                {menu.items.map((item) => (
                  <Link href={item.href} key={item.href} onClick={closeMobile}>
                    {item.label}
                  </Link>
                ))}
              </div>
            ))}
            {audienceLinks.map((item) => (
              <Link
                className="mobile-menu-audience"
                href={item.href}
                key={item.href}
                onClick={closeMobile}
              >
                {item.label}
              </Link>
            ))}
            <Link
              className="mobile-menu-audience"
              href="/judge"
              onClick={closeMobile}
            >
              Judge walkthrough
            </Link>
            <Link
              className="mobile-menu-audience"
              href="/evidence"
              onClick={closeMobile}
            >
              Evidence map
            </Link>
            <Link href="/login" onClick={closeMobile}>
              Log in
            </Link>
            <Button href="/contact" variant="primary">
              Submit a project <ArrowRight size={16} aria-hidden="true" />
            </Button>
            <Button href="/for-students" variant="secondary">
              Apply as a student
            </Button>
          </nav>
        </>
      ) : null}
    </header>
  );
}
