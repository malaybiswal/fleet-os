"use client";

import React from "react";
import { usePathname } from "next/navigation";

const pageTitles: Record<string, string> = {
  "/":      "Dashboard",
  "/dwell": "Dwell Analytics",
};

export function Topbar() {
  const pathname = usePathname();
  const title = pageTitles[pathname] ?? "Fleet OS";
  const date = new Date().toLocaleDateString("en-US", {
    weekday: "short", month: "short", day: "numeric", year: "numeric",
  });

  return (
    <header className="flex items-center justify-between border-b border-zinc-800 bg-zinc-950 px-6 py-4">
      <h2 className="text-base font-semibold text-zinc-50">{title}</h2>
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-1.5 text-xs text-zinc-500">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-green-500" />
          Live
        </span>
        <span className="text-xs text-zinc-600">{date}</span>
      </div>
    </header>
  );
}
