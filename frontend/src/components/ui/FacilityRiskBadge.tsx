import React from "react";

import FacilityRiskDetails from "@/components/ui/FacilityRiskDetails";
import type { FacilityRiskSummary } from "@/types";

type Props = {
  facilityRisk?: FacilityRiskSummary | null;
};

const bandStyles: Record<string, string> = {
  low: "bg-green-100 text-green-700",
  medium: "bg-amber-100 text-amber-700",
  high: "bg-red-100 text-red-700",
};

const bandLabels: Record<string, string> = {
  low: "Low Risk",
  medium: "Medium Risk",
  high: "High Risk",
};

export default function FacilityRiskBadge({ facilityRisk }: Props) {
  if (!facilityRisk || facilityRisk.detention_risk_band === null) {
    return (
      <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-500">
        No data
      </span>
    );
  }

  const band = facilityRisk.detention_risk_band;
  const className = bandStyles[band] ?? "bg-slate-100 text-slate-700";
  const label = bandLabels[band] ?? band;

  return (
    <span className="group relative inline-flex">
      <span
        className={`rounded-full px-2 py-1 text-xs font-medium ${className}`}
      >
        {label}
      </span>

      <span className="pointer-events-none absolute left-1/2 top-full z-10 mt-2 w-56 -translate-x-1/2 rounded-lg border border-slate-200 bg-white p-3 text-left text-xs text-slate-700 opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
        <FacilityRiskDetails facilityRisk={facilityRisk} />
      </span>
    </span>
  );
}
