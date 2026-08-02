import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

const praxisSans = localFont({
  src: "./fonts/noto-sans.ttf",
  variable: "--font-sans",
});

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
      <body className={praxisSans.variable}>{children}</body>
    </html>
  );
}
