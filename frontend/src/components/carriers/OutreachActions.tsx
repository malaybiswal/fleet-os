"use client";

import { useState } from "react";

import { logContact, updateOutreachStatus } from "@/lib/api";
import type { CarrierDetail, CarrierListItem } from "@/types";
import {
  OUTREACH_OPTIONS,
  OUTREACH_STYLES,
  relativeContactTime,
} from "./outreach";

type Props = {
  carrier: CarrierListItem;
  onUpdated: (carrier: CarrierDetail) => void;
  variant?: "full" | "compact";
};

// Stop card-level navigation when actions are embedded in a clickable card.
function stop(e: React.SyntheticEvent) {
  e.stopPropagation();
}

export function OutreachActions({ carrier, onUpdated, variant = "full" }: Props) {
  const [busy, setBusy] = useState(false);
  const compact = variant === "compact";

  async function handleLog(method: "call" | "email") {
    if (busy) return;
    setBusy(true);
    try {
      const updated = await logContact(carrier.id, { method });
      onUpdated(updated);
    } finally {
      setBusy(false);
    }
  }

  async function handleStatus(status: string) {
    if (busy || status === carrier.outreach_status) return;
    setBusy(true);
    try {
      const updated = await updateOutreachStatus(carrier.id, status);
      onUpdated(updated);
    } finally {
      setBusy(false);
    }
  }

  const lastContacted = relativeContactTime(carrier.last_contacted_at);
  const btn =
    "rounded-md border px-2.5 py-1 text-xs font-medium transition-colors disabled:opacity-50";

  return (
    <div className={compact ? "space-y-2" : "space-y-3"}>
      <div className="flex flex-wrap items-center gap-2">
        {carrier.phone && (
          <a
            href={`tel:${carrier.phone}`}
            onClick={stop}
            className={`${btn} border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100`}
          >
            Call
          </a>
        )}
        {carrier.email && (
          <a
            href={`mailto:${carrier.email}`}
            onClick={stop}
            className={`${btn} border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100`}
          >
            Email
          </a>
        )}
        <button
          type="button"
          disabled={busy}
          onClick={(e) => {
            stop(e);
            handleLog("call");
          }}
          className={`${btn} border-slate-200 text-slate-600 hover:bg-slate-100`}
        >
          Log Call
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={(e) => {
            stop(e);
            handleLog("email");
          }}
          className={`${btn} border-slate-200 text-slate-600 hover:bg-slate-100`}
        >
          Log Email
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
            OUTREACH_STYLES[carrier.outreach_status] ?? "bg-slate-100 text-slate-600"
          }`}
        >
          📞 {carrier.contact_attempts}
          {lastContacted ? ` · ${lastContacted}` : ""}
        </span>
        {!compact && (
          <select
            value={carrier.outreach_status}
            disabled={busy}
            onClick={stop}
            onChange={(e) => {
              stop(e);
              handleStatus(e.target.value);
            }}
            className="rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
            aria-label="Outreach status"
          >
            {OUTREACH_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  );
}
