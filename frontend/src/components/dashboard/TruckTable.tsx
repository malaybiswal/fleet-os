import type { Truck } from "@/types";

export function TruckTable({ trucks }: { trucks: Truck[] }) {
  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900">Truck Status</h3>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-500">
            <tr>
              <th className="py-2">Truck</th>
              <th className="py-2">Status</th>
              <th className="py-2">Location</th>
              <th className="py-2">Last Seen</th>
            </tr>
          </thead>
          <tbody>
            {trucks.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-4 text-slate-500">
                  No trucks available.
                </td>
              </tr>
            ) : (
              trucks.map((truck) => (
                <tr key={truck.truck_id} className="border-t">
                  <td className="py-3 font-medium text-slate-900">
                    {truck.truck_id}
                  </td>
                  <td className="py-3">
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                      {truck.status}
                    </span>
                  </td>
                  <td className="py-3 text-slate-600">
                    {truck.current_location ?? "Unknown"}
                  </td>
                  <td className="py-3 text-slate-500">
                    {truck.last_seen_at
                      ? new Date(truck.last_seen_at).toLocaleString()
                      : "N/A"}
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