"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import LoadsTable, { type Load } from "@/components/tables/LoadsTable";
import { getLoads } from "@/lib/api";

export default function LoadsPage() {
  const { isAuthenticated, isLoading } = useAuth();

  const [loads, setLoads] = useState<Load[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isLoading || !isAuthenticated) {
      return;
    }

    async function fetchLoads() {
      try {
        const data = await getLoads();
        setLoads(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load loads");
      } finally {
        setLoading(false);
      }
    }

    fetchLoads();
  }, [isAuthenticated, isLoading]);

  if (isLoading || loading) {
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