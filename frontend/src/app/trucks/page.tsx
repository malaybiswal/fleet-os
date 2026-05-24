"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import TrucksPageTable, {
  type Truck,
} from "@/components/tables/TrucksPageTable";
import { getTrucks } from "@/lib/api";

export default function TrucksPage() {
  const { isAuthenticated, isLoading } = useAuth();

  const [trucks, setTrucks] = useState<Truck[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isLoading || !isAuthenticated) {
      return;
    }

    async function fetchTrucks() {
      try {
        const data = await getTrucks();

        setTrucks(
          data.map((truck) => ({
            ...truck,
            current_lat:
              truck.current_lat === null || truck.current_lat === undefined
                ? null
                : Number(truck.current_lat),
            current_lon:
              truck.current_lon === null || truck.current_lon === undefined
                ? null
                : Number(truck.current_lon),
          })),
        );
      } catch (err) {
        console.error(err);
        setError("Failed to load trucks");
      } finally {
        setLoading(false);
      }
    }

    fetchTrucks();
  }, [isAuthenticated, isLoading]);

  if (isLoading || loading) {
    return <div className="p-6 text-slate-700">Loading trucks...</div>;
  }

  if (error) {
    return <div className="p-6 text-red-500">{error}</div>;
  }

  return (
    <main className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Trucks</h1>
        <p className="text-slate-500">
          Fleet equipment status, location, and telemetry visibility
        </p>
      </div>

      <TrucksPageTable trucks={trucks} />
    </main>
  );
}