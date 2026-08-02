import { Command } from "lucide-react";
import Link from "next/link";

export function Brand() {
  return (
    <Link className="brand" href="/" aria-label="PraxisAI home">
      <span className="brand-mark" aria-hidden="true">
        <Command size={19} />
      </span>
      <span>PraxisAI</span>
    </Link>
  );
}
