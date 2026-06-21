import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "../globals.css";

import { UserMenu } from "@/components/auth/UserMenu";
import { Sidebar } from "@/components/layout/Sidebar";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { AuthGuard } from "@/components/auth/AuthGuard";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Fleet OS",
  description: "Fleet Operating System dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans text-content antialiased">
        <AuthProvider>
          <AuthGuard>
            <div className="flex min-h-screen bg-canvas">
              <Sidebar />

              <main className="flex-1 overflow-y-auto bg-canvas">
                <header className="sticky top-0 z-20 flex items-center justify-between border-b border-border bg-surface/80 px-6 py-3 backdrop-blur">
                  <span className="font-mono text-[11px] uppercase tracking-widest text-content-muted">
                    Control Tower
                  </span>
                  <UserMenu />
                </header>

                <div className="mx-auto max-w-screen-xl p-6">{children}</div>
              </main>
            </div>
          </AuthGuard>
        </AuthProvider>
      </body>
    </html>
  );
}
