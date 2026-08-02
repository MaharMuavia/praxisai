import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "PraxisAI", template: "%s · PraxisAI" },
  description:
    "Small paid client projects, operated with AI and released through qualified human oversight.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
