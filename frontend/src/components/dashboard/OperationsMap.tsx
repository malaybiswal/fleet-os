import React from "react";
import type { Truck } from "@/types";


export function OperationsMap({ trucks }: { trucks: Truck[] }) {
  const gpsCount = trucks.filter((t) => t.current_lat && t.current_lon).length;

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
      <h3 className="text-sm font-semibold text-zinc-50">Operations Map</h3>
      <p className="mt-0.5 text-xs text-zinc-500">
        Map visualization placeholder using current_lat/current_lon.
      </p>

      <div className="mt-4 rounded-md border border-zinc-800 bg-zinc-950 px-5 py-8 text-sm text-zinc-500">
        {gpsCount} trucks have GPS coordinates available.
      </div>
    </div>
  );
}
