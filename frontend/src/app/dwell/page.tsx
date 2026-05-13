"use client";

import React, { useEffect, useState } from "react";

import DwellBarChart from "@/components/charts/DwellBarChart";
import BrokerBarChart from "@/components/charts/BrokerBarChart";
import DetentionChart from "@/components/charts/DetentionChart";
import FacilityScorecard from "@/components/tables/FacilityScorecard";

export default function DwellPage() {
  const [facilityData, setFacilityData] = useState<any[]>([]);
  const [brokerData, setBrokerData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchData() {
      try {
        const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
        const [facilityRes, brokerRes] = await Promise.all([
          fetch(`${base}/api/dwell/facility-scorecard`),
          fetch(`${base}/api/dwell/broker-scorecard`),
        ]);

        setFacilityData(await facilityRes.json());
        setBrokerData(await brokerRes.json());
      } catch {
        setError("Failed to load dwell analytics");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return <div className="p-6 text-sm text-zinc-500">Loading dwell analytics...</div>;
  }

  if (error) {
    return <div className="p-6 text-sm text-red-400">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-zinc-50">Dwell Analytics</h1>
        <p className="mt-0.5 text-xs text-zinc-500">Facility dwell time and detention insights</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <DwellBarChart data={facilityData} />
        <BrokerBarChart data={brokerData} />
      </div>

      <DetentionChart data={facilityData} />

      <FacilityScorecard data={facilityData} />
    </div>
  );
}
