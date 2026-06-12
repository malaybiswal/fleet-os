import React from "react";

import type { FacilityRiskSummary } from "@/types";

type Props = {
  facilityRisk: FacilityRiskSummary;
};

export function formatHours(value: number | null) {
  if (value === null) return "—";
  return `${value.toFixed(1)}h`;
}

export function formatPercent(value: number | null) {
  if (value === null) return "—";
  return `${value.toFixed(0)}%`;
}

export function formatScore(value: number | null) {
  if (value === null) return "—";
  return value.toFixed(0);
}

export default function FacilityRiskDetails({ facilityRisk }: Props) {
  return (
    <>
      <span className="block font-semibold text-slate-900">
        {facilityRisk.facility_name}
      </span>
      <span className="mt-1 block">
        Operational score: {formatScore(facilityRisk.operational_score)}/100
      </span>
      <span className="block">
        Est. unload delay: {formatHours(facilityRisk.avg_dwell_hours)} avg /{" "}
        {formatHours(facilityRisk.p90_dwell_hours)} worst-case
      </span>
      <span className="block">
        Appointment reliability:{" "}
        {formatPercent(facilityRisk.appointment_reliability_pct)}
      </span>
      <span className="block">
        Detention risk score: {formatScore(facilityRisk.detention_risk_score)}
        /100
      </span>
      <span className="mt-1 block text-slate-500">
        Based on {facilityRisk.visit_count} visit
        {facilityRisk.visit_count === 1 ? "" : "s"} ({facilityRisk.confidence}{" "}
        confidence)
      </span>
    </>
  );
}
