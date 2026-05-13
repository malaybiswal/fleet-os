"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { label: "Dashboard", href: "/",      icon: "⊞" },
  { label: "Dwell",     href: "/dwell", icon: "⏱" },
  { label: "Trucks",    href: "#",      icon: "🚛" },
  { label: "Alerts",    href: "#",      icon: "🔔" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden min-h-screen w-60 flex-col bg-slate-900 md:flex">
      <div className="border-b border-slate-700 px-6 py-5">
        <span className="text-lg font-bold text-white">Fleet OS</span>
        <p className="mt-0.5 text-xs text-slate-400">Control Tower</p>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map(({ label, href, icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={label}
              href={href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-slate-700 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <span className="text-base">{icon}</span>
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-700 px-6 py-4">
        <p className="text-xs text-slate-500">fleet-os v1.0</p>
      </div>
    </aside>
  );
}
