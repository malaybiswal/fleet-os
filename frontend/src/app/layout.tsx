import type { Metadata } from "next";
import "../globals.css";

import { UserMenu } from "@/components/auth/UserMenu";
import { Sidebar } from "@/components/layout/Sidebar";

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
    <html lang="en">
      <body>
        <div className="flex min-h-screen bg-slate-50">
          <Sidebar />

          <main className="flex-1 overflow-y-auto bg-slate-50">
            <header className="flex justify-end border-b bg-white px-6 py-3">
              <UserMenu />
            </header>

            <div className="mx-auto max-w-screen-xl p-6">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}