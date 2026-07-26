import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentOps — autonomous infra agent, observed",
  description: "A DevOps agent that investigates and acts on your fleet, with every step traced and destructive actions gated on human approval.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans bg-base text-ink min-h-screen">{children}</body>
    </html>
  );
}
