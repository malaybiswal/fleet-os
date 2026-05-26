"use client";

import type { Tag } from "@/types";

export type CarrierFilterState = {
  state: string;
  authority_status: string;
  power_units_min: string;
  power_units_max: string;
  authority_age_days: string;
  outreach_status: string;
  tag: string;
  cargo_type: string;
  order_by: string;
};

export const DEFAULT_FILTERS: CarrierFilterState = {
  state: "",
  authority_status: "",
  power_units_min: "",
  power_units_max: "",
  authority_age_days: "",
  outreach_status: "",
  tag: "",
  cargo_type: "",
  order_by: "",
};

const AUTHORITY_STATUSES = ["active", "inactive", "pending"];
const CARGO_TYPES = [
  "General Freight",
  "Household Goods",
  "Metal: sheets, coils, rolls",
  "Motor Vehicles",
  "Drive/Tow away",
  "Logs, Poles, Beams, Lumber",
  "Building Materials",
  "Mobile Homes",
  "Machinery, Large Objects",
  "Fresh Produce",
  "Liquids/Gases",
  "Intermodal Cont.",
  "Passengers",
  "Oilfield Equipment",
  "Livestock",
  "Grain, Feed, Hay",
  "Coal/Coke",
  "Meat",
  "Garbage/Refuse",
  "US Mail",
  "Chemicals",
  "Commodities Dry Bulk",
  "Refrigerated Food",
  "Beverages",
  "Paper Products",
  "Utilities",
  "Agricultural/Farm Supplies",
  "Construction",
  "Water Well",
  "Other",
];
const OUTREACH_STATUSES = [
  { value: "not_contacted", label: "Not Contacted" },
  { value: "contacted", label: "Contacted" },
  { value: "follow_up", label: "Follow Up" },
  { value: "not_interested", label: "Not Interested" },
  { value: "converted", label: "Converted" },
];

type Props = {
  filters: CarrierFilterState;
  onChange: (filters: CarrierFilterState) => void;
  tags: Tag[];
};

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-slate-500">{label}</label>
      {children}
    </div>
  );
}

const inputCls =
  "rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400";

export function CarrierFilters({ filters, onChange, tags }: Props) {
  function set(key: keyof CarrierFilterState, value: string) {
    onChange({ ...filters, [key]: value });
  }

  function reset() {
    onChange(DEFAULT_FILTERS);
  }

  const hasActive = Object.values(filters).some((v) => v !== "");

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-end gap-3">
        <Field label="State">
          <input
            type="text"
            maxLength={2}
            placeholder="e.g. TX"
            value={filters.state}
            onChange={(e) => set("state", e.target.value.toUpperCase())}
            className={`w-20 ${inputCls}`}
          />
        </Field>

        <Field label="Authority Status">
          <select
            value={filters.authority_status}
            onChange={(e) => set("authority_status", e.target.value)}
            className={inputCls}
          >
            <option value="">Any</option>
            {AUTHORITY_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Min Fleet">
          <input
            type="number"
            min={0}
            placeholder="0"
            value={filters.power_units_min}
            onChange={(e) => set("power_units_min", e.target.value)}
            className={`w-20 ${inputCls}`}
          />
        </Field>

        <Field label="Max Fleet">
          <input
            type="number"
            min={0}
            placeholder="∞"
            value={filters.power_units_max}
            onChange={(e) => set("power_units_max", e.target.value)}
            className={`w-20 ${inputCls}`}
          />
        </Field>

        <Field label="Authority Age ≤ (days)">
          <input
            type="number"
            min={0}
            placeholder="Any"
            value={filters.authority_age_days}
            onChange={(e) => set("authority_age_days", e.target.value)}
            className={`w-28 ${inputCls}`}
          />
        </Field>

        <Field label="Outreach Status">
          <select
            value={filters.outreach_status}
            onChange={(e) => set("outreach_status", e.target.value)}
            className={inputCls}
          >
            <option value="">Any</option>
            {OUTREACH_STATUSES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Cargo Type">
          <select
            value={filters.cargo_type}
            onChange={(e) => set("cargo_type", e.target.value)}
            className={inputCls}
          >
            <option value="">Any</option>
            {CARGO_TYPES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Tag">
          <select
            value={filters.tag}
            onChange={(e) => set("tag", e.target.value)}
            className={inputCls}
          >
            <option value="">Any</option>
            {tags.map((t) => (
              <option key={t.id} value={t.name}>
                {t.display_name ?? t.name}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Sort">
          <select
            value={filters.order_by}
            onChange={(e) => set("order_by", e.target.value)}
            className={inputCls}
          >
            <option value="">Default (Lead Score)</option>
            <option value="lead_score_desc">Lead Score</option>
            <option value="authority_date_desc">Newest Authority</option>
            <option value="power_units_desc">Largest Fleet</option>
            <option value="created_at_desc">Newest Ingested</option>
            <option value="id_asc">Oldest Ingested</option>
          </select>
        </Field>

        {hasActive && (
          <button
            onClick={reset}
            className="rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-500 hover:bg-slate-50"
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );
}
