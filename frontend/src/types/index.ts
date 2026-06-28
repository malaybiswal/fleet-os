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
  contact_attempts: number;
  last_contacted_at: string | null;
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

export type Load = {
  id: number;
  load_id: string;
  truck_id?: string | null;
  driver_id?: string | null;
  equipment_type?: string | null;
  broker_name?: string | null;
  origin?: string | null;
  origin_lat?: string | number | null;
  origin_lon?: string | number | null;
  destination?: string | null;
  revenue?: string | number | null;
  miles?: string | number | null;
  deadhead_miles?: string | number | null;
  fuel_cost?: string | number | null;
  maintenance_reserve?: string | number | null;
  driver_cost?: string | number | null;
  tolls?: string | number | null;
  status: string;
  source?: string | null;
  external_ref?: string | null;
  last_synced_at?: string | null;
  pickup_time?: string | null;
  delivery_time?: string | null;
  facility_risk?: FacilityRiskSummary | null;
};

export type DatIntegrationStatus = {
  connected: boolean;
  status: string;
  last_sync_at?: string | null;
  last_error?: string | null;
  service_account_email?: string | null;
  user_email?: string | null;
  base_url?: string | null;
  filters?: Record<string, unknown>;
};

export type DatCredentialRequest = {
  service_account_email: string;
  service_account_password: string;
  user_email: string;
  base_url?: string | null;
  filters?: Record<string, unknown>;
};

export type DatSyncAccepted = {
  status: string;
  detail: string;
};

export type TruckstopIntegrationStatus = {
  connected: boolean;
  status: string;
  last_sync_at?: string | null;
  last_error?: string | null;
  integration_id?: string | null;
  username?: string | null;
  base_url?: string | null;
  filters?: Record<string, unknown>;
};

export type TruckstopCredentialRequest = {
  integration_id: string;
  username: string;
  password: string;
  base_url?: string | null;
  filters?: Record<string, unknown>;
};

export type TruckstopSyncAccepted = {
  status: string;
  detail: string;
};

export type LoadEvaluationMetrics = {
  gross_rpm: number;
  deadhead_adjusted_rpm: number;
  estimated_fuel_cost: number;
  estimated_revenue_per_hour: number;
  deadhead_penalty: number;
  estimated_drive_hours: number;
  expected_dwell_hours: number;
  profitability_score: number;
  operational_score: number;
  profitability_factors: {
    margin_score: number;
    net_rpm_score: number;
    revenue_per_hour_score: number;
  };
  net_margin: number;
  stored_costs_used: boolean;
};

export type LoadRecommendation = "RECOMMENDED" | "REVIEW" | "AVOID";

export type EvaluatedMockLoad = {
  name: string;
  description: string;
  payout: number;
  loaded_miles: number;
  deadhead_miles: number;
  equipment_type: "Dry Van" | "Reefer" | "Flatbed" | "Power Only";
  expected_recommendation: LoadRecommendation;
  actual_recommendation: LoadRecommendation;
  metrics: LoadEvaluationMetrics;
  reasons: string[];
  destination_facility?: FacilityRiskSummary | null;
};

export type DispatcherRecommendation = "RECOMMENDED" | "REVIEW" | "AVOID";

export type DispatcherScoreBreakdown = {
  profitability_baseline: number;
  facility_multiplier: number;
  broker_multiplier: number;
  alert_penalty: number;
  strategy_bonus: number;
  final_dispatch_score: number;
};

export type DispatcherDecisionMetrics = Omit<LoadEvaluationMetrics, "expected_dwell_hours"> & {
  deadhead_miles: number;
  broker_risk_band: "low" | "medium" | "high";
  expected_dwell_hours: number | null;
  facility_detention_risk_band: DetentionRiskBand | null;
  profitability_baseline: number | null;
  facility_multiplier: number | null;
  broker_multiplier: number | null;
  alert_penalty: number | null;
  strategy_bonus: number | null;
  final_dispatch_score: number | null;
};

export type DispatcherTruckOption = {
  truck_id: string;
  driver_id: string;
  driver_name: string;
  driver_hos_hours_remaining: number | null;
  status: string;
  current_location: string | null;
  latitude: number | null;
  longitude: number | null;
  last_seen_at: string | null;
  active_alert_count: number;
  highest_alert_severity: string | null;
  recommendation: DispatcherRecommendation;
  rank_score: number;
  deadhead_miles: number;
  deadhead_source: string;
  can_make_pickup: boolean;
  estimated_revenue_per_hour: number;
  profitability_score: number;
  operational_score: number;
  score_breakdown: DispatcherScoreBreakdown;
  reasons: string[];
  ranking_factors: string[];
};

export type DispatcherCommandCenterDecision = {
  load: Load;
  best_truck: DispatcherTruckOption | null;
  truck_options: DispatcherTruckOption[];
  facility_risk: FacilityRiskSummary | null;
  final_recommendation: DispatcherRecommendation;
  metrics: DispatcherDecisionMetrics;
  reasons: string[];
  decision_notes: string[];
  is_candidate: boolean;
};
