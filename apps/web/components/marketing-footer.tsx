import Link from "next/link";
import { Brand } from "./brand";

const columns = [
  {
    title: "Platform",
    links: [
      ["How it works", "/how-it-works"],
      ["For students", "/for-students"],
      ["For companies", "/for-companies"],
      ["Solutions", "/solutions"],
      ["Pricing", "/pricing"],
    ],
  },
  {
    title: "Community",
    links: [
      ["Expert leads", "/for-expert-leads"],
      ["Universities", "/for-universities"],
      ["Impact", "/impact"],
      ["About PraxisAI", "/about"],
      ["Contact", "/contact"],
    ],
  },
  {
    title: "Trust & safety",
    links: [
      ["Trust model", "/trust"],
      ["AI governance", "/trust/ai-governance"],
      ["Student protection", "/trust/student-protection"],
      ["Data & privacy", "/trust/data-and-privacy"],
      ["Accessibility", "/accessibility"],
    ],
  },
];

export function MarketingFooter() {
  return (
    <footer className="marketing-footer">
      <div className="marketing-footer-grid">
        <div className="marketing-footer-intro">
          <Brand />
          <p>
            The AI-operated apprenticeship studio for real preparation, paid
            project experience, and verified career proof.
          </p>
        </div>
        {columns.map((column) => (
          <div key={column.title}>
            <h2>{column.title}</h2>
            <ul>
              {column.links.map(([label, href]) => (
                <li key={href}>
                  <Link href={href}>{label}</Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="marketing-footer-bottom">
        <span>
          © {new Date().getFullYear()} PraxisAI. Built for accountable
          opportunity.
        </span>
        <span className="marketing-footer-legal">
          <Link href="/privacy">Privacy</Link>
          <Link href="/terms">Terms</Link>
        </span>
      </div>
    </footer>
  );
}
