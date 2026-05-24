"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { getLivePositions, type LiveTruckPosition } from "@/lib/api";

export default function LivePositionsPage() {
  const { isAuthenticated, isLoading } = useAuth();

  const [positions, setPositions] = useState<LiveTruckPosition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isLoading || !isAuthenticated) {
      return;
    }

    async function fetchPositions() {
      try {
        const data = await getLivePositions();
        setPositions(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load live positions");
      } finally {
        setLoading(false);
      }
    }

    fetchPositions();
  }, [isAuthenticated, isLoading]);

  if (isLoading || loading) {
    return <div className="p-6 text-slate-700">Loading live positions...</div>;
  }

  if (error) {
    return <div className="p-6 text-red-500">{error}</div>;
  }

  return (
    <main className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">
          Live Fleet Positions
        </h1>
        <p className="text-slate-500">
          Authenticated live truck telemetry from FleetOS ingestion pipeline
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Truck
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Status
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Location
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Latitude
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Longitude
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Speed
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">
                Last Seen
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {positions.map((position) => (
              <tr key={position.truck_id}>
                <td className="px-4 py-3 font-medium text-slate-900">
                  {position.truck_id}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {position.status}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {position.current_location ?? "-"}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {position.latitude ?? "-"}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {position.longitude ?? "-"}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {position.speed === null ? "-" : `${position.speed} mph`}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {position.last_seen_at
                    ? new Date(position.last_seen_at).toLocaleString()
                    : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {positions.length === 0 && (
          <div className="p-6 text-sm text-slate-500">
            No live positions found for this fleet.
          </div>
        )}
      </div>
    </main>
  );
}
