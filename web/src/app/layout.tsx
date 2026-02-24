import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Gong Call Chunker",
  description: "Extract structured intelligence from sales calls",
};

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/calls", label: "Calls" },
  { href: "/schemas", label: "Schemas" },
  { href: "/analytics", label: "Analytics" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900">
        <div className="flex min-h-screen">
          {/* Sidebar */}
          <nav className="w-56 bg-gray-900 text-white flex flex-col p-4 gap-1">
            <h1 className="text-lg font-bold mb-6 px-3">Call Chunker</h1>
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="px-3 py-2 rounded hover:bg-gray-800 transition-colors text-sm"
              >
                {item.label}
              </Link>
            ))}
          </nav>

          {/* Main content */}
          <main className="flex-1 p-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
