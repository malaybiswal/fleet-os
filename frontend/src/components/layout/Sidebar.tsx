const navItems = [
  "Dashboard",
  "Trucks",
  "Telemetry",
  "Dwell",
  "Alerts",
];

export function Sidebar() {
  return (
    <aside className="hidden min-h-screen w-64 border-r bg-white p-6 md:block">
      <h1 className="text-xl font-bold text-slate-900">Fleet OS</h1>
      <p className="mt-1 text-sm text-slate-500">Control Tower</p>

      <nav className="mt-8 space-y-2">
        {navItems.map((item) => (
          <div
            key={item}
            className="rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            {item}
          </div>
        ))}
      </nav>
    </aside>
  );
}