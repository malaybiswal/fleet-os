"use client";

import { useState } from "react";

import type { Truck } from "@/types";

const STATUS_BADGE: Record<string, string> = {
  active: "bg-emerald-100 text-emerald-700",
  idle: "bg-amber-100 text-amber-700",
  maintenance: "bg-red-100 text-red-700",
};

const STATUS_FILTERS = ["all", "active", "idle", "maintenance"] as const;

export function TruckTable({ trucks }: { trucks: Truck[] }) {
  const [filter, setFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const filtered = trucks.filter((t) => {
    const matchesText =
      t.truck_id.toLowerCase().includes(filter.toLowerCase()) ||
      (t.current_location ?? "").toLowerCase().includes(filter.toLowerCase());
    const matchesStatus =
      statusFilter === "all" || t.status === statusFilter;
    return matchesText && matchesStatus;
  });

  const visible = filtered.slice(0, 10);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-slate-900">Truck Fleet</h3>
        <p className="text-sm text-slate-500">Manage your trucks.</p>
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[180px]">
          <svg
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            viewBox="0 0 24 24"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <input
            type="text"
            placeholder="Filter trucks..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-4 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
          />
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {STATUS_FILTERS.map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`rounded-full px-3 py-1 text-xs font-medium capitalize transition-colors ${
                statusFilter === s
                  ? "bg-slate-900 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              <th className="pb-3 pr-4">Truck</th>
              <th className="pb-3 pr-4">Status</th>
              <th className="pb-3 pr-4">Location</th>
              <th className="pb-3">Last Seen</th>
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-8 text-center text-slate-500">
                  No trucks found.
                </td>
              </tr>
            ) : (
              <>
                {visible.map((truck) => (
                  <tr
                    key={truck.truck_id}
                    className="border-t border-slate-100 transition-colors hover:bg-slate-50"
                  >
                    <td className="py-3 pr-4 font-medium text-slate-900">
                      {truck.truck_id}
                    </td>
                    <td className="py-3 pr-4">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${
                          STATUS_BADGE[truck.status] ?? "bg-slate-100 text-slate-600"
                        }`}
                      >
                        {truck.status}
                      </span>
                    </td>
                    <td className="py-3 pr-4 text-sm text-slate-600">
                      {truck.current_location ?? "Unknown"}
                    </td>
                    <td className="py-3 text-xs text-slate-400">
                      {truck.last_seen_at
                        ? new Date(truck.last_seen_at).toLocaleString()
                        : "N/A"}
                    </td>
                  </tr>
                ))}
                {filtered.length > 10 && (
                  <tr>
                    <td
                      colSpan={4}
                      className="pt-3 text-center text-xs text-blue-600"
                    >
                      +{filtered.length - 10} more trucks
                    </td>
                  </tr>
                )}
              </>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
