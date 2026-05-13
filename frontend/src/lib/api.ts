import type { Alert, DashboardSummary, Truck } from "@/types";

const API_BASE_URL =
  process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
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

export function getAlerts(): Promise<Alert[]> {
  return fetchJson<Alert[]>("/api/alerts?resolved=false");
}