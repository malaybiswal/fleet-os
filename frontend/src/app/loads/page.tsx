"use client";

import { useEffect, useState } from "react";

import LoadsTable, { type Load } from "@/components/tables/LoadsTable";

export default function LoadsPage() {
  const [loads, setLoads] = useState<Load[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchLoads() {
      try {
        const response = await fetch("http://localhost:8000/api/loads");

        if (!response.ok) {
          throw new Error("Failed to fetch loads");
        }

        const data = await response.json();
        setLoads(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load loads");
      } finally {
        setLoading(false);
      }
    }

    fetchLoads();
  }, []);

  if (loading) {
    return <div className="p-6 text-slate-700">Loading loads...</div>;
  }

  if (error) {
    return <div className="p-6 text-red-500">{error}</div>;
  }

  return (
    <main className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Loads</h1>
        <p className="text-slate-500">
          Fleet load profitability and operational analytics
        </p>
      </div>

      <LoadsTable loads={loads} />
    </main>
  );
}