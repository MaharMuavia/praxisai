import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { Brand } from "./brand";

export function MarketingNav() {
  return (
    <header className="topbar">
      <Brand />
      <nav className="topnav" aria-label="Primary navigation">
        <Link href="/how-it-works/clients">For clients</Link>
        <Link href="/how-it-works/students">For students</Link>
        <Link href="/trust">Trust model</Link>
        <Link href="/login" className="button button-primary">
          Enter workspace <ArrowRight size={15} />
        </Link>
      </nav>
    </header>
  );
}
