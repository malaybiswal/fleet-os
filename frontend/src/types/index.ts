export type Paginated<T> = {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
};

export type CarrierListItem = {
  id: number;
  dot_number: string;
  mc_number: string | null;
  legal_name: string;
  dba_name: string | null;
  phone: string | null;
  email: string | null;
  address_line1: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  country: string | null;
  authority_status: string | null;
  authority_date: string | null;
  power_units: number | null;
  driver_count: number | null;
  cargo_types: string[] | null;
  lead_score: number | null;
  outreach_status: string;
  created_at: string;
  updated_at: string;
};

export type CarrierDetail = CarrierListItem;

export type OutreachNote = {
  id: number;
  carrier_id: number;
  content: string;
  outcome: string | null;
  follow_up_date: string | null;
  contact_name: string | null;
  dispatcher_name: string | null;
  pain_points: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
};

export type Tag = {
  id: number;
  name: string;
  display_name: string | null;
  created_at: string;
  updated_at: string;
};

export type CarrierPipelineStats = {
  total: number;
  new_last_30_days: number;
  avg_lead_score: number | null;
  not_contacted: number;
};

export type DashboardSummary = {
  active_trucks: number;
  avg_dwell_hours: number;
  total_revenue: string;
  avg_revenue_per_mile: string;
  deadhead_percentage: number;
  open_alerts: number;
  open_loads: number;
  fuel_cost_per_mile: string;
};

export type Truck = {
  id: number;
  truck_id: string;
  status: string;
  current_location?: string | null;
  current_lat?: string | null;
  current_lon?: string | null;
  last_seen_at?: string | null;
  created_at: string;
};

export type Alert = {
  id: number;
  truck_id: string;
  severity: string;
  alert_type: string;
  message?: string | null;
  created_at: string;
  resolved: boolean;
};

export type DetentionRiskBand = "low" | "medium" | "high";

export type FacilityRiskSummary = {
  facility_id: number | null;
  facility_name: string;
  operational_score: number | null;
  avg_dwell_hours: number | null;
  p90_dwell_hours: number | null;
  appointment_reliability_pct: number | null;
  detention_risk_score: number | null;
  detention_risk_band: DetentionRiskBand | null;
  visit_count: number;
  confidence: "low" | "medium" | "high";
};

export type FacilityIntelligence = FacilityRiskSummary & {
  city: string | null;
  state: string | null;
  latitude: number | null;
  longitude: number | null;
  facility_type: string | null;
  dwell_score: number | null;
  avg_appointment_delay_hours: number | null;
  total_detention_pay: string;
  last_visit_at: string | null;
};
