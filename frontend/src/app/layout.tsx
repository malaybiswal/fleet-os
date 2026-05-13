import React from "react";
import type { Metadata } from "next";
import "../globals.css";

import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

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
        <div className="flex min-h-screen bg-zinc-950">
          <Sidebar />
          <main className="flex min-h-screen flex-1 flex-col">
            <Topbar />
            <div className="flex-1 p-6">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}