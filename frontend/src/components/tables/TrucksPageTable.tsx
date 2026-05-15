import React from "react";

import StatusBadge from "@/components/ui/StatusBadge";

export type Truck = {
  id: number;
  truck_id: string;
  status: string;
  current_location?: string | null;
  current_lat?: number | null;
  current_lon?: number | null;
  last_seen_at?: string | null;
  created_at?: string | null;
};

type Props = {
  trucks?: Truck[];
};

function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

export default function TrucksPageTable({ trucks = [] }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900">Truck List</h2>
        <p className="text-sm text-slate-500">
          Current truck status, location, and last seen telemetry
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-[900px] divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Truck
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Status
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Current Location
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Latitude
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Longitude
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Last Seen
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Created
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-100">
            {trucks.map((truck) => (
              <tr key={truck.id} className="hover:bg-slate-50">
                <td className="whitespace-nowrap px-4 py-3 font-semibold text-slate-900">
                  {truck.truck_id}
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  <StatusBadge status={truck.status} />
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                  {truck.current_location ?? "—"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                  {truck.current_lat ?? "—"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                  {truck.current_lon ?? "—"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                  {formatDate(truck.last_seen_at)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                  {formatDate(truck.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}