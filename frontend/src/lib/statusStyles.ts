/**
 * Single source of truth for status / severity / risk badge styling.
 *
 * Tones blend design-system token backgrounds (`*-soft`) with legible
 * dark text. Add or re-map keys here — every badge consumes these maps,
 * so theming stays one file deep.
 */

export type Tone = "ok" | "warn" | "danger" | "info" | "neutral";

/** Tailwind classes for each semantic tone (background + text). */
export const toneClass: Record<Tone, string> = {
  ok: "bg-ok-soft text-emerald-700",
  warn: "bg-warn-soft text-amber-700",
  danger: "bg-danger-soft text-red-700",
  info: "bg-accent-soft text-accent",
  neutral: "bg-surface-sunken text-content-secondary",
};

/** Operational / lifecycle status → tone. */
const statusTone: Record<string, Tone> = {
  delivered: "ok",
  moving: "ok",
  active: "ok",
  in_transit: "info",
  idle: "info",
  booked: "warn",
  slow: "warn",
  cancelled: "danger",
  maintenance: "danger",
  stopped: "neutral",
};

/** Alert severity → tone. */
const severityTone: Record<string, Tone> = {
  high: "danger",
  medium: "warn",
  low: "ok",
};

/** Facility detention-risk band → tone. */
const riskBandTone: Record<string, Tone> = {
  low: "ok",
  medium: "warn",
  high: "danger",
};

const FALLBACK: Tone = "neutral";

export function statusToneClass(status: string): string {
  return toneClass[statusTone[status.toLowerCase()] ?? FALLBACK];
}

export function severityToneClass(severity: string): string {
  return toneClass[severityTone[severity.toLowerCase()] ?? FALLBACK];
}

export function riskBandToneClass(band: string): string {
  return toneClass[riskBandTone[band.toLowerCase()] ?? FALLBACK];
}
