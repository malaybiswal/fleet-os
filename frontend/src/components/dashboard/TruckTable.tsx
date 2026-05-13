import React from "react";
import type { Truck } from "@/types";

const statusStyles: Record<string, string> = {
  active:      "bg-green-500/10 text-green-400 border border-green-500/20",
  idle:        "bg-zinc-500/10 text-zinc-400 border border-zinc-500/20",
  maintenance: "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20",
};

export function TruckTable({ trucks }: { trucks: Truck[] }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
      <h3 className="text-sm font-semibold text-zinc-50">Truck Status</h3>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-zinc-800">
              <th className="pb-3 text-xs font-medium uppercase tracking-wide text-zinc-500">Truck</th>
              <th className="pb-3 text-xs font-medium uppercase tracking-wide text-zinc-500">Status</th>
              <th className="pb-3 text-xs font-medium uppercase tracking-wide text-zinc-500">Location</th>
              <th className="pb-3 text-xs font-medium uppercase tracking-wide text-zinc-500">Last Seen</th>
            </tr>
          </thead>
          <tbody>
            {trucks.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-4 text-zinc-500">
                  No trucks available.
                </td>
              </tr>
            ) : (
              trucks.map((truck) => (
                <tr key={truck.truck_id} className="border-t border-zinc-800/50">
                  <td className="py-3 font-medium text-zinc-200">{truck.truck_id}</td>
                  <td className="py-3">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusStyles[truck.status.toLowerCase()] ?? statusStyles.idle}`}>
                      {truck.status}
                    </span>
                  </td>
                  <td className="py-3 text-zinc-400">{truck.current_location ?? "Unknown"}</td>
                  <td className="py-3 text-zinc-500">
                    {truck.last_seen_at ? new Date(truck.last_seen_at).toLocaleString() : "N/A"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
