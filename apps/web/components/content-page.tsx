import { ArrowRight, CheckCircle2 } from "lucide-react";
import { MarketingFooter } from "./marketing-footer";
import { MarketingNav } from "./marketing-nav";
import { Button } from "./ui";

export function ContentPage({
  title,
  eyebrow,
  description,
  points,
}: {
  title: string;
  eyebrow: string;
  description: string;
  points: string[];
}) {
  return (
    <main id="main-content" className="marketing-site">
      <MarketingNav />
      <section className="content-page-hero">
        <div className="marketing-container content-page-hero-inner">
          <p className="marketing-eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
      </section>
      <section className="marketing-section content-page-body">
        <div className="marketing-container content-page-grid">
          <div>
            <p className="marketing-eyebrow">The PraxisAI approach</p>
            <h2>Clear boundaries make useful work possible.</h2>
            <p className="content-page-intro">
              This page describes the operating model and the commitments
              supported by the current product and policy surface. Where a
              workflow still needs backend support, the next step is stated
              plainly.
            </p>
          </div>
          <div className="content-page-points">
            {points.map((point, index) => (
              <article key={point}>
                <span className="content-point-index">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <CheckCircle2 size={19} aria-hidden="true" />
                <p>{point}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
      <section className="marketing-section content-page-cta">
        <div className="marketing-container">
          <h2>Choose a path into the studio.</h2>
          <p>
            Read the role-specific journey, or sign in to an existing workspace
            when your organization has been onboarded.
          </p>
          <div className="marketing-actions">
            <Button href="/for-students" variant="secondary">
              For students <ArrowRight size={16} aria-hidden="true" />
            </Button>
            <Button href="/for-companies" variant="primary">
              For companies <ArrowRight size={16} aria-hidden="true" />
            </Button>
          </div>
        </div>
      </section>
      <MarketingFooter />
    </main>
  );
}
