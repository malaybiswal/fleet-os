"use client";

import { useEffect, useState } from "react";

import BrokerBarChart from "@/components/charts/BrokerBarChart";
import DetentionChart from "@/components/charts/DetentionChart";
import DwellBarChart from "@/components/charts/DwellBarChart";
import { useAuth } from "@/components/auth/AuthProvider";
import FacilityScorecard from "@/components/tables/FacilityScorecard";
import {
  getDwellBrokerScorecard,
  getDwellFacilityScorecard,
  type DwellBrokerScore,
  type DwellFacilityScore,
} from "@/lib/api";

export default function DwellPage() {
  const { isAuthenticated, isLoading } = useAuth();

  const [facilityData, setFacilityData] = useState<DwellFacilityScore[]>([]);
  const [brokerData, setBrokerData] = useState<DwellBrokerScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isLoading || !isAuthenticated) {
      return;
    }

    async function fetchData() {
      try {
        const [facilityJson, brokerJson] = await Promise.all([
          getDwellFacilityScorecard(),
          getDwellBrokerScorecard(),
        ]);

        setFacilityData(
          facilityJson.map((row) => ({
            ...row,
            avg_loading_delay_hours: row.avg_loading_delay_hours ?? 0,
            total_detention_pay: String(row.total_detention_pay ?? "0"),
          })),
        );
        setBrokerData(
          brokerJson.map((row) => ({
            ...row,
            avg_loading_delay_hours: row.avg_loading_delay_hours ?? 0,
            total_detention_pay: String(row.total_detention_pay ?? "0"),
            load_count: row.load_count ?? 0,
          })),
        );
      } catch (err) {
        console.error(err);
        setError("Failed to load dwell analytics");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [isAuthenticated, isLoading]);

  if (isLoading || loading) {
    return <div className="p-6">Loading dwell analytics...</div>;
  }

  if (error) {
    return <div className="p-6 text-red-500">{error}</div>;
  }

  return (
    <main className="space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold">Dwell Analytics</h1>
        <p className="text-gray-500">
          Facility dwell time and detention insights
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <DwellBarChart data={facilityData} />
        <BrokerBarChart data={brokerData} />
      </div>

      <DetentionChart data={facilityData} />

      <FacilityScorecard data={facilityData} />
    </main>
  );
}