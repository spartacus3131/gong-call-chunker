import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";
import Providers from "@/components/Providers";
import UserMenu from "@/components/UserMenu";
import OnboardingGuard from "@/components/OnboardingGuard";

export const metadata: Metadata = {
  title: "Gong Call Chunker",
  description: "Extract structured intelligence from sales calls",
};

const navItems = [
  { href: "/", label: "Dashboard", icon: ">" },
  { href: "/calls", label: "Calls", icon: ">" },
  { href: "/schemas", label: "Schemas", icon: ">" },
  { href: "/analytics", label: "Analytics", icon: ">" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <div className="flex min-h-screen">
            {/* FF7-style sidebar */}
            <nav className="w-56 bg-ff-panel border-r border-ff-border flex flex-col p-4 gap-1">
              <div className="mb-6 px-3">
                <h1 className="text-mako-400 font-bold text-lg tracking-wide">
                  CALL CHUNKER
                </h1>
                <div className="h-px bg-gradient-to-r from-mako-500/50 to-transparent mt-2" />
              </div>
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="px-3 py-2 rounded text-sm text-ff-text hover:text-mako-400 hover:bg-mako-500/5 transition-colors flex items-center gap-2"
                >
                  <span className="text-mako-600 text-xs">{item.icon}</span>
                  {item.label}
                </Link>
              ))}
              <div className="mt-auto pt-4 border-t border-ff-border/50">
                <UserMenu />
                <p className="text-[10px] text-ff-text/30 px-3 mt-2">
                  v2.0 // MAKO POWERED
                </p>
              </div>
            </nav>

            {/* Main content */}
            <main className="flex-1 p-8 overflow-auto">
              <OnboardingGuard>{children}</OnboardingGuard>
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
