import type { Truck } from "@/types";

export function OperationsMap({ trucks }: { trucks: Truck[] }) {
  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900">Operations Map</h3>
      <p className="text-sm text-slate-500">
        Map visualization placeholder using current_lat/current_lon.
      </p>

      <div className="mt-4 rounded-xl bg-slate-100 p-6 text-sm text-slate-600">
        {trucks.filter((truck) => truck.current_lat && truck.current_lon).length}{" "}
        trucks have GPS coordinates available.
      </div>
    </div>
  );
}