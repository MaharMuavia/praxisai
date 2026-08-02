import { MarketingNav } from "./marketing-nav";

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
    <main className="content-page">
      <MarketingNav />
      <section className="content-hero">
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </section>
      <section className="content-body">
        <h2>What to expect</h2>
        <div className="principles">
          {points.map((point, index) => (
            <article className="principle" key={point}>
              <span className="step-number">0{index + 1}</span>
              <p>{point}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
