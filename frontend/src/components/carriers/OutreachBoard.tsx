"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { listCarriers, updateOutreachStatus } from "@/lib/api";
import type { CarrierListItem } from "@/types";
import { formatPhone } from "@/lib/utils";
import {
  OUTREACH_ORDER,
  OUTREACH_STYLES,
  outreachLabel,
  type OutreachStatus,
} from "./outreach";

export type Columns = Record<OutreachStatus, CarrierListItem[]>;

const PER_COLUMN = 25;

function emptyColumns(): Columns {
  return Object.fromEntries(
    OUTREACH_ORDER.map((s) => [s, []]),
  ) as unknown as Columns;
}

// Pure move helper (exported for unit tests): move a carrier between columns and
// update its outreach_status. Returns a new Columns object; never mutates input.
export function moveCarrierBetweenColumns(
  columns: Columns,
  carrierId: number,
  from: OutreachStatus,
  to: OutreachStatus,
): Columns {
  if (from === to) return columns;
  const carrier = columns[from]?.find((c) => c.id === carrierId);
  if (!carrier) return columns;
  return {
    ...columns,
    [from]: columns[from].filter((c) => c.id !== carrierId),
    [to]: [{ ...carrier, outreach_status: to }, ...columns[to]],
  };
}

export function OutreachBoard() {
  const router = useRouter();
  const [columns, setColumns] = useState<Columns>(emptyColumns);
  const [dragging, setDragging] = useState<
    { id: number; from: OutreachStatus } | null
  >(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all(
      OUTREACH_ORDER.map((status) =>
        listCarriers({ outreach_status: status, page_size: PER_COLUMN }).then(
          (res) => [status, res.data] as const,
        ),
      ),
    )
      .then((entries) => {
        setColumns(Object.fromEntries(entries) as Columns);
      })
      .finally(() => setLoading(false));
  }, []);

  async function handleDrop(to: OutreachStatus) {
    const drag = dragging;
    setDragging(null);
    if (!drag || drag.from === to) return;

    const previous = columns;
    setColumns((cols) => moveCarrierBetweenColumns(cols, drag.id, drag.from, to));
    try {
      await updateOutreachStatus(drag.id, to);
    } catch {
      setColumns(previous); // revert on failure
    }
  }

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white px-4 py-12 text-center text-sm text-slate-400 shadow-sm">
        Loading pipeline…
      </div>
    );
  }

  return (
    <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-5">
      {OUTREACH_ORDER.map((status) => (
        <div
          key={status}
          onDragOver={(e) => e.preventDefault()}
          onDrop={() => handleDrop(status)}
          className="flex min-h-[8rem] flex-col rounded-xl border border-slate-200 bg-slate-50 p-3"
          data-testid={`column-${status}`}
        >
          <div className="mb-2 flex items-center justify-between">
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                OUTREACH_STYLES[status] ?? "bg-slate-100 text-slate-600"
              }`}
            >
              {outreachLabel(status)}
            </span>
            <span className="text-xs text-slate-400">{columns[status].length}</span>
          </div>

          <div className="flex flex-col gap-2">
            {columns[status].map((carrier) => (
              <div
                key={carrier.id}
                draggable
                onDragStart={() => setDragging({ id: carrier.id, from: status })}
                onDragEnd={() => setDragging(null)}
                onClick={() => router.push(`/carriers/${carrier.id}`)}
                className="cursor-grab rounded-lg border border-slate-200 bg-white p-3 text-sm shadow-sm hover:shadow active:cursor-grabbing"
              >
                <p className="font-medium text-slate-800">{carrier.legal_name}</p>
                <p className="text-xs text-slate-500">
                  {[carrier.city, carrier.state].filter(Boolean).join(", ") ||
                    "Location unknown"}
                </p>
                <div className="mt-1 flex items-center justify-between text-xs text-slate-400">
                  <span>📞 {carrier.contact_attempts}</span>
                  {carrier.phone && <span>{formatPhone(carrier.phone)}</span>}
                </div>
              </div>
            ))}
            {columns[status].length === 0 && (
              <p className="text-xs text-slate-400">No carriers.</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
