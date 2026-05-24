import { auth } from "@/lib/firebase";
import type { Alert, DashboardSummary, Truck } from "@/types";
import type { Load } from "@/components/tables/LoadsTable";

export type CurrentUser = {
  id: number;
  firebase_uid: string;
  email: string;
  name: string | null;
  role: string;
  fleet_id: number;
};

export type DwellFacilityScore = {
  facility_name: string;
  avg_dwell_hours: number;
  avg_loading_delay_hours: number;
  total_detention_pay: string;
  visit_count: number;
  facility_score: number;
};

export type DwellBrokerScore = {
  broker_name: string;
  avg_dwell_hours: number;
  avg_loading_delay_hours: number;
  total_detention_pay: string;
  load_count: number;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  process.env.INTERNAL_API_URL ??
  "http://localhost:8000";

async function fetchJson<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);

  const currentUser = auth.currentUser;

  if (currentUser) {
    const token = await currentUser.getIdToken();

    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    cache: "no-store",
    headers,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getDashboardSummary(): Promise<DashboardSummary> {
  return fetchJson<DashboardSummary>("/api/dashboard/summary");
}

export function getTrucks(): Promise<Truck[]> {
  return fetchJson<Truck[]>("/api/trucks");
}

export function getLoads(): Promise<Load[]> {
  return fetchJson<Load[]>("/api/loads");
}

export function getAlerts(): Promise<Alert[]> {
  return fetchJson<Alert[]>("/api/alerts?resolved=false");
}

export function resolveAlert(alertId: number): Promise<Alert> {
  return fetchJson<Alert>(`/api/alerts/${alertId}/resolve`, {
    method: "PATCH",
  });
}

export function getDwellFacilityScorecard(): Promise<DwellFacilityScore[]> {
  return fetchJson<DwellFacilityScore[]>("/api/dwell/facility-scorecard");
}

export function getDwellBrokerScorecard(): Promise<DwellBrokerScore[]> {
  return fetchJson<DwellBrokerScore[]>("/api/dwell/broker-scorecard");
}

export function getCurrentUser(): Promise<CurrentUser> {
  return fetchJson<CurrentUser>("/api/me");
}