"use client";

import type { CSSProperties, HTMLAttributes, ReactNode } from "react";
import { useEffect, useRef, useState } from "react";

type MotionProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  delay?: number;
};

function useInView() {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "0px 0px -8%" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return { ref, visible };
}

function MotionBlock({
  children,
  className = "",
  delay = 0,
  ...props
}: MotionProps) {
  const { ref, visible } = useInView();
  const style = {
    ...props.style,
    "--motion-delay": `${delay}ms`,
  } as CSSProperties;
  return (
    <div
      {...props}
      className={`${className} motion-block ${visible ? "is-visible" : ""}`.trim()}
      ref={ref}
      style={style}
    >
      {children}
    </div>
  );
}

export function FadeIn(props: MotionProps) {
  return (
    <MotionBlock
      {...props}
      className={`motion-fade ${props.className ?? ""}`}
    />
  );
}

export function Reveal(props: MotionProps) {
  return (
    <MotionBlock
      {...props}
      className={`motion-reveal ${props.className ?? ""}`}
    />
  );
}

export function Stagger({ children, className = "", ...props }: MotionProps) {
  return (
    <MotionBlock {...props} className={`motion-stagger ${className}`}>
      {children}
    </MotionBlock>
  );
}

export function ScaleIn(props: MotionProps) {
  return (
    <MotionBlock
      {...props}
      className={`motion-scale ${props.className ?? ""}`}
    />
  );
}

export function SlideIn(props: MotionProps) {
  return (
    <MotionBlock
      {...props}
      className={`motion-slide ${props.className ?? ""}`}
    />
  );
}

export function MotionCard(props: MotionProps) {
  return (
    <Reveal {...props} className={`motion-card ${props.className ?? ""}`} />
  );
}

export function AnimatedPresencePanel({
  children,
  className = "",
  panelKey,
}: MotionProps & { panelKey: string }) {
  return (
    <div
      key={panelKey}
      className={`animated-panel ${className}`}
      data-panel-key={panelKey}
    >
      {children}
    </div>
  );
}

export function PageTransition(props: MotionProps) {
  return (
    <FadeIn {...props} className={`page-transition ${props.className ?? ""}`} />
  );
}

export function MotionButton({
  children,
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode }) {
  return (
    <button {...props} className={`motion-button ${className}`.trim()}>
      {children}
    </button>
  );
}

export function WorkflowMotion({
  children,
  className = "",
  ...props
}: MotionProps) {
  return (
    <Reveal {...props} className={`workflow-motion ${className}`}>
      {children}
    </Reveal>
  );
}

export function AnimatedNumber({
  value,
  format = "number",
  currency = "USD",
}: {
  value: number;
  format?: "number" | "currency" | "percent";
  currency?: string;
}) {
  const [displayValue, setDisplayValue] = useState(value);
  const previousValue = useRef(value);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReducedMotion(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    if (reducedMotion || previousValue.current === value) {
      previousValue.current = value;
      setDisplayValue(value);
      return;
    }
    const start = previousValue.current;
    const delta = value - start;
    const startedAt = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const progress = Math.min((now - startedAt) / 420, 1);
      const eased = 1 - (1 - progress) ** 3;
      setDisplayValue(start + delta * eased);
      if (progress < 1) frame = requestAnimationFrame(tick);
      else previousValue.current = value;
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [reducedMotion, value]);

  const formatter = new Intl.NumberFormat(undefined, {
    style: format === "currency" ? "currency" : "decimal",
    currency: format === "currency" ? currency : undefined,
    maximumFractionDigits: format === "percent" ? 1 : 0,
  });
  const formatted =
    format === "percent"
      ? `${formatter.format(displayValue)}%`
      : formatter.format(displayValue);
  return (
    <span className="animated-number" aria-label={formatted}>
      {formatted}
    </span>
  );
}

export function ScrollProgress() {
  const [progress, setProgress] = useState(0);
  useEffect(() => {
    let frame = 0;
    let lastProgress = -1;
    const update = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const next = max > 0 ? Math.min(window.scrollY / max, 1) : 0;
      if (Math.abs(next - lastProgress) > 0.002) {
        lastProgress = next;
        setProgress(next);
      }
      frame = 0;
    };
    const schedule = () => {
      if (frame === 0) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule, { passive: true });
    const observer =
      typeof ResizeObserver === "undefined"
        ? null
        : new ResizeObserver(schedule);
    observer?.observe(document.documentElement);
    return () => {
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
      observer?.disconnect();
      if (frame) cancelAnimationFrame(frame);
    };
  }, []);
  return (
    <span
      className="scroll-progress"
      style={{ transform: `scaleX(${progress})` }}
    />
  );
}
