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
    <div className={`animated-panel ${className}`} data-panel-key={panelKey}>
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

export function AnimatedNumber({ value }: { value: string | number }) {
  return <span className="animated-number">{value}</span>;
}

export function ScrollProgress() {
  const [progress, setProgress] = useState(0);
  useEffect(() => {
    const update = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      setProgress(max > 0 ? Math.min(window.scrollY / max, 1) : 0);
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    return () => window.removeEventListener("scroll", update);
  }, []);
  return (
    <span
      className="scroll-progress"
      style={{ transform: `scaleX(${progress})` }}
    />
  );
}
