import { auth } from "@/lib/firebase";
import type {
  Alert,
  CarrierDetail,
  CarrierListItem,
  CarrierPipelineStats,
  DashboardSummary,
  FacilityIntelligence,
  OutreachNote,
  Paginated,
  Tag,
  Truck,
} from "@/types";
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

export type LiveTruckPosition = {
  truck_id: string;
  status: string;
  latitude: number | null;
  longitude: number | null;
  speed: number | null;
  heading: number | null;
  last_seen_at: string | null;
  current_location: string | null;
  active_alert_count: number;
  highest_alert_severity: string | null;
  active_alerts: Array<{
    id: number;
    severity: string;
    alert_type: string;
    message: string | null;
    created_at: string;
  }>;
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

  if (response.status === 204) {
    return undefined as T;
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

export function getLivePositions(): Promise<LiveTruckPosition[]> {
  return fetchJson<LiveTruckPosition[]>("/api/fleet/live-positions");
}

export function getFacilities(): Promise<FacilityIntelligence[]> {
  return fetchJson<FacilityIntelligence[]>("/api/facilities");
}

// ---------------------------------------------------------------------------
// Carriers
// ---------------------------------------------------------------------------

type CarrierListParams = {
  state?: string;
  authority_status?: string;
  power_units_min?: number;
  power_units_max?: number;
  authority_age_days?: number;
  outreach_status?: string;
  tag?: string;
  cargo_type?: string;
  order_by?: string;
  page?: number;
  page_size?: number;
};

function buildQuery(params: Record<string, string | number | undefined>): string {
  const qs = new URLSearchParams();
  for (const [key, val] of Object.entries(params)) {
    if (val !== undefined && val !== "") qs.set(key, String(val));
  }
  const str = qs.toString();
  return str ? `?${str}` : "";
}

export function getCarrierPipelineStats(): Promise<CarrierPipelineStats> {
  return fetchJson<CarrierPipelineStats>("/api/carriers/pipeline-stats");
}

export function listCarriers(params: CarrierListParams = {}): Promise<Paginated<CarrierListItem>> {
  return fetchJson<Paginated<CarrierListItem>>(`/api/carriers${buildQuery(params as Record<string, string | number | undefined>)}`);
}

export function searchCarriers(q: string, page = 1, page_size = 50): Promise<Paginated<CarrierListItem>> {
  return fetchJson<Paginated<CarrierListItem>>(`/api/carriers/search${buildQuery({ q, page, page_size })}`);
}

export function getCarrier(id: number): Promise<CarrierDetail> {
  return fetchJson<CarrierDetail>(`/api/carriers/${id}`);
}

export function updateOutreachStatus(id: number, status: string): Promise<CarrierDetail> {
  return fetchJson<CarrierDetail>(`/api/carriers/${id}/outreach-status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
}

export function listNotes(carrierId: number): Promise<OutreachNote[]> {
  return fetchJson<OutreachNote[]>(`/api/carriers/${carrierId}/notes`);
}

export function createNote(
  carrierId: number,
  data: { content: string; outcome?: string; follow_up_date?: string; dispatcher_name?: string },
): Promise<OutreachNote> {
  return fetchJson<OutreachNote>(`/api/carriers/${carrierId}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updateNote(
  carrierId: number,
  noteId: number,
  data: { content?: string; outcome?: string; follow_up_date?: string | null },
): Promise<OutreachNote> {
  return fetchJson<OutreachNote>(`/api/carriers/${carrierId}/notes/${noteId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function deleteNote(carrierId: number, noteId: number): Promise<void> {
  return fetchJson<void>(`/api/carriers/${carrierId}/notes/${noteId}`, { method: "DELETE" });
}

export function listCarrierTags(carrierId: number): Promise<Tag[]> {
  return fetchJson<Tag[]>(`/api/carriers/${carrierId}/tags`);
}

export function listTags(): Promise<Tag[]> {
  return fetchJson<Tag[]>("/api/tags");
}

export function createTag(name: string): Promise<Tag> {
  return fetchJson<Tag>("/api/tags", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

export function addTagToCarrier(carrierId: number, tagId: number): Promise<Tag[]> {
  return fetchJson<Tag[]>(`/api/carriers/${carrierId}/tags`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tag_id: tagId }),
  });
}

export function removeTagFromCarrier(carrierId: number, tagId: number): Promise<void> {
  return fetchJson<void>(`/api/carriers/${carrierId}/tags/${tagId}`, { method: "DELETE" });
}
