"use client";

import { useEffect, useState } from "react";

import TrucksPageTable, {
  type Truck,
} from "@/components/tables/TrucksPageTable";

export default function TrucksPage() {
  const [trucks, setTrucks] = useState<Truck[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchTrucks() {
      try {
        const response = await fetch("http://localhost:8000/api/trucks");

        if (!response.ok) {
          throw new Error("Failed to fetch trucks");
        }

        const data = await response.json();
        setTrucks(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load trucks");
      } finally {
        setLoading(false);
      }
    }

    fetchTrucks();
  }, []);

  if (loading) {
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