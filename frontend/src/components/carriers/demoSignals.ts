import type { CarrierListItem } from "@/types";

export const NEW_AUTHORITY_MAX_DAYS = 365;
export const GROWTH_FLEET_MIN_UNITS = 5;
export const GROWTH_FLEET_MAX_UNITS = 25;
export const HOT_PROSPECT_SCORE = 60;
export const WARM_PROSPECT_SCORE = 40;

export type ProspectTier = "hot" | "warm" | "cold";

export function authorityAgeDays(authorityDate: string | null): number | null {
  if (!authorityDate) return null;
  return Math.floor((Date.now() - new Date(authorityDate).getTime()) / 86_400_000);
}

export function isNewAuthority(carrier: CarrierListItem): boolean {
  const days = authorityAgeDays(carrier.authority_date);
  return days !== null && days >= 0 && days <= NEW_AUTHORITY_MAX_DAYS;
}

export function isGrowthFleet(carrier: CarrierListItem): boolean {
  const units = carrier.power_units;
  return units !== null && units >= GROWTH_FLEET_MIN_UNITS && units <= GROWTH_FLEET_MAX_UNITS;
}

export function prospectTier(carrier: CarrierListItem): ProspectTier {
  const score = carrier.lead_score ?? 0;
  if (score >= HOT_PROSPECT_SCORE) return "hot";
  if (score >= WARM_PROSPECT_SCORE) return "warm";
  return "cold";
}

export function formatFleetSize(powerUnits: number | null): string {
  if (powerUnits === null) return "Fleet size unknown";
  return `${powerUnits} truck${powerUnits === 1 ? "" : "s"}`;
}
