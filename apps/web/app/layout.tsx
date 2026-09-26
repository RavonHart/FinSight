import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinSight — AI Financial Research & Investment Learning",
  description: "Production-style multi-user AI investment research, portfolio analysis, deterministic simulation, and financial learning platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-[#090d16] text-slate-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
