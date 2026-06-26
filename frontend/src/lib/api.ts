import { auth } from "@/lib/firebase";
import type {
  Alert,
  CarrierDetail,
  CarrierListItem,
  CarrierPipelineStats,
  DashboardSummary,
  DatCredentialRequest,
  DatIntegrationStatus,
  DatSyncAccepted,
  DispatcherCommandCenterDecision,
  EvaluatedMockLoad,
  FacilityIntelligence,
  Load,
  OutreachNote,
  Paginated,
  Tag,
  Truck,
} from "@/types";

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

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

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
    throw new ApiError(
      response.status,
      (await readApiErrorMessage(response)) ?? `API request failed: ${response.status}`,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

async function readApiErrorMessage(response: Response): Promise<string | null> {
  try {
    const body = (await response.json()) as { error?: unknown; detail?: unknown };
    if (typeof body.error === "string" && body.error.trim()) {
      return body.error;
    }
    if (typeof body.detail === "string" && body.detail.trim()) {
      return body.detail;
    }
  } catch {
    return null;
  }

  return null;
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

export function getDispatcherCandidates(): Promise<Load[]> {
  return fetchJson<Load[]>("/api/dispatcher-command-center/candidates");
}

export function getDispatcherDecision(
  loadId: string,
): Promise<DispatcherCommandCenterDecision> {
  return fetchJson<DispatcherCommandCenterDecision>(
    `/api/dispatcher-command-center/loads/${encodeURIComponent(loadId)}/decision`,
  );
}

export function acceptDispatcherRecommendation(
  loadId: string,
  truckId: string,
  driverId: string,
): Promise<Load> {
  return fetchJson<Load>(
    `/api/dispatcher-command-center/loads/${encodeURIComponent(loadId)}/assign`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        truck_id: truckId,
        driver_id: driverId,
      }),
    },
  );
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

export function getDemoMockLoads(): Promise<EvaluatedMockLoad[]> {
  return fetchJson<EvaluatedMockLoad[]>("/api/load-evaluation/mock-loads");
}

export function getDatIntegration(): Promise<DatIntegrationStatus> {
  return fetchJson<DatIntegrationStatus>("/api/integrations/dat");
}

export function connectDatCredentials(
  body: DatCredentialRequest,
): Promise<DatIntegrationStatus> {
  return fetchJson<DatIntegrationStatus>("/api/integrations/dat", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function testDatConnection(): Promise<{ success: boolean; message: string }> {
  return fetchJson<{ success: boolean; message: string }>("/api/integrations/dat/test", {
    method: "POST",
  });
}

export function triggerDatSync(): Promise<DatSyncAccepted> {
  return fetchJson<DatSyncAccepted>("/api/integrations/dat/sync", {
    method: "POST",
  });
}

export function disconnectDat(): Promise<DatIntegrationStatus> {
  return fetchJson<DatIntegrationStatus>("/api/integrations/dat", {
    method: "DELETE",
  });
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

export function listNewCarriers(days = 30, page = 1, page_size = 50): Promise<Paginated<CarrierListItem>> {
  return fetchJson<Paginated<CarrierListItem>>(`/api/carriers/new${buildQuery({ days, page, page_size })}`);
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

export function logContact(
  carrierId: number,
  data: { method: string; outcome?: string; note?: string; advance_status?: boolean },
): Promise<CarrierDetail> {
  return fetchJson<CarrierDetail>(`/api/carriers/${carrierId}/log-contact`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
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
