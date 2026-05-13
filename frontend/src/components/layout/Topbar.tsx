"use client";

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
    <header className="flex items-center justify-between border-b bg-white px-6 py-4">
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-1.5 text-xs text-slate-500">
          <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
          Live
        </span>
        <span className="text-xs text-slate-400">{date}</span>
      </div>
    </header>
  );
}
