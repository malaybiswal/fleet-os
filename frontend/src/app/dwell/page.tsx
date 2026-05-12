"use client";

import { useEffect, useState } from "react";

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
      console.log("Fetching dwell analytics...");

      const [facilityRes, brokerRes] = await Promise.all([
        fetch("http://localhost:8000/api/dwell/facility-scorecard"),
        fetch("http://localhost:8000/api/dwell/broker-scorecard"),
      ]);

      console.log("facilityRes", facilityRes.status);
      console.log("brokerRes", brokerRes.status);

      const facilityJson = await facilityRes.json();
      const brokerJson = await brokerRes.json();

      console.log("facilityJson", facilityJson);
      console.log("brokerJson", brokerJson);

      setFacilityData(facilityJson);
      setBrokerData(brokerJson);
    } catch (err) {
      console.error("FETCH ERROR:", err);
      setError("Failed to load dwell analytics");
    } finally {
      console.log("Loading complete");
      setLoading(false);
    }
  }

  fetchData();
}, []);

  if (loading) {
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