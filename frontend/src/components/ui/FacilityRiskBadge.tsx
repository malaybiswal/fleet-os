import React from "react";

import FacilityRiskDetails from "@/components/ui/FacilityRiskDetails";
import { riskBandToneClass } from "@/lib/statusStyles";
import type { FacilityRiskSummary } from "@/types";

type Props = {
  facilityRisk?: FacilityRiskSummary | null;
};

const bandLabels: Record<string, string> = {
  low: "Low Risk",
  medium: "Medium Risk",
  high: "High Risk",
};

export default function FacilityRiskBadge({ facilityRisk }: Props) {
  if (!facilityRisk || facilityRisk.detention_risk_band === null) {
    return (
      <span className="rounded-full bg-surface-sunken px-2 py-1 text-xs font-medium text-content-muted">
        No data
      </span>
    );
  }

  const band = facilityRisk.detention_risk_band;
  const className = riskBandToneClass(band);
  const label = bandLabels[band] ?? band;

  return (
    <span className="group relative inline-flex">
      <span
        className={`rounded-full px-2 py-1 text-xs font-medium ${className}`}
      >
        {label}
      </span>

      <span className="pointer-events-none absolute left-1/2 top-full z-10 mt-2 w-56 -translate-x-1/2 rounded-card border border-border bg-surface p-3 text-left text-xs text-content-secondary opacity-0 shadow-overlay transition-opacity group-hover:opacity-100">
        <FacilityRiskDetails facilityRisk={facilityRisk} />
      </span>
    </span>
  );
}
