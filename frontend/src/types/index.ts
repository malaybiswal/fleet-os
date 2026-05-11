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