import { auth } from "@/lib/firebase";
import type { Alert, DashboardSummary, Truck } from "@/types";

export type CurrentUser = {
  id: number;
  firebase_uid: string;
  email: string;
  name: string | null;
  role: string;
  fleet_id: number;
};

const API_BASE_URL =
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

async function fetchJson<T>(path: string): Promise<T> {
  const headers: HeadersInit = {};

  const currentUser = auth.currentUser;

  if (currentUser) {
    const token = await currentUser.getIdToken();

    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
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

export function getAlerts(): Promise<Alert[]> {
  return fetchJson<Alert[]>("/api/alerts?resolved=false");
}

export function getCurrentUser(): Promise<CurrentUser> {
  return fetchJson<CurrentUser>("/api/me");
}