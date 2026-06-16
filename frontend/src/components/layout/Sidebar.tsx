"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

function DashboardIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" />
      <rect x="14" y="3" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" />
    </svg>
  );
}

function DwellIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}

function TruckIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="1" y="3" width="15" height="13" />
      <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
      <circle cx="5.5" cy="18.5" r="2.5" />
      <circle cx="18.5" cy="18.5" r="2.5" />
    </svg>
  );
}

function MapIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21 3 6" />
      <line x1="9" y1="3" x2="9" y2="18" />
      <line x1="15" y1="6" x2="15" y2="21" />
    </svg>
  );
}

function LoadIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 7h13v10H3z" />
      <path d="M16 10h3l2 3v4h-5z" />
      <circle cx="7.5" cy="18.5" r="1.5" />
      <circle cx="18.5" cy="18.5" r="1.5" />
    </svg>
  );
}

function BellIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 01-3.46 0" />
    </svg>
  );
}

function CarrierIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

function GearIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
    </svg>
  );
}

function NavItem({
  href,
  icon,
  label,
  active,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
        active
          ? "border-l-2 border-blue-500 bg-slate-700 pl-[10px] text-white"
          : "text-slate-300 hover:bg-slate-800 hover:text-white"
      }`}
    >
      <span className="h-4 w-4 flex-shrink-0">{icon}</span>
      {label}
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex flex-col min-h-screen w-56 bg-slate-900">
      <div className="px-6 py-5 border-b border-slate-800">
        <span className="block text-white font-bold text-lg">Fleet OS</span>
        <span className="text-slate-500 text-xs block mt-0.5">Control Tower</span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-6 overflow-y-auto">
        <div>
          <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
            Fleet
          </p>
          <div className="space-y-1">
            <NavItem href="/" icon={<DashboardIcon />} label="Dashboard" active={pathname === "/"} />
            <NavItem href="/dwell" icon={<DwellIcon />} label="Dwell Analytics" active={pathname === "/dwell"} />
          </div>
        </div>

        <div className="border-t border-slate-800" />

        <div>
          <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
            Operations
          </p>
          <div className="space-y-1">
            <NavItem href="/trucks" icon={<TruckIcon />} label="Trucks" active={pathname === "/trucks"} />
            <NavItem href="/live" icon={<MapIcon />} label="Live Map" active={pathname === "/live"} />
            <NavItem href="/loads" icon={<LoadIcon />} label="Loads" active={pathname === "/loads"} />
            <NavItem href="/load-evaluation" icon={<LoadIcon />} label="Load Evaluation" active={pathname === "/load-evaluation"}/>
            <NavItem href="/alerts" icon={<BellIcon />} label="Alerts" active={pathname === "/alerts"} />
            <NavItem href="/carriers" icon={<CarrierIcon />} label="Carriers" active={pathname === "/carriers"} />
            <NavItem href="/carriers/demo" icon={<CarrierIcon />} label="Prospects (Demo)" active={pathname === "/carriers/demo"} />
            <NavItem href="/demo" icon={<MapIcon />} label="Demo Stories" active={pathname === "/demo"} />
            <NavItem href="/demo/script" icon={<MapIcon />} label="60-Second Demo" active={pathname === "/demo/script"} />
          </div>
        </div>

        <div className="border-t border-slate-800" />

        <div>
          <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
            Settings
          </p>
          <div className="space-y-1">
            <NavItem href="/settings" icon={<GearIcon />} label="Settings" active={pathname === "/settings"} />
          </div>
        </div>
      </nav>

      <div className="px-6 py-4 border-t border-slate-800">
        <span className="text-slate-500 text-xs">v1.0.0</span>
      </div>
    </aside>
  );
}
