"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { formatPhone } from "@/lib/utils";
import type { CarrierListItem } from "@/types";

const OUTREACH_STYLES: Record<string, string> = {
  not_contacted: "bg-slate-100 text-slate-600",
  contacted: "bg-blue-100 text-blue-700",
  follow_up: "bg-yellow-100 text-yellow-700",
  not_interested: "bg-red-100 text-red-600",
  converted: "bg-emerald-100 text-emerald-700",
};

function OutreachBadge({ status }: { status: string }) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-semibold capitalize ${
        OUTREACH_STYLES[status] ?? "bg-slate-100 text-slate-600"
      }`}
    >
      {status.replaceAll("_", " ")}
    </span>
  );
}

function authorityAge(authorityDate: string | null): string {
  if (!authorityDate) return "—";
  const days = Math.floor(
    (Date.now() - new Date(authorityDate).getTime()) / 86_400_000,
  );
  if (days < 365) return `${days}d`;
  const years = (days / 365).toFixed(1);
  return `${years}y`;
}

type Props = {
  carriers: CarrierListItem[];
  total: number;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
};

export function CarriersTable({
  carriers,
  total,
  page,
  totalPages,
  onPageChange,
}: Props) {
  const router = useRouter();

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-[1100px] divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Company</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">DOT</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">MC</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">State</th>
              <th className="px-4 py-3 text-right font-semibold text-slate-700">Fleet</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Cargo</th>
              <th className="px-4 py-3 text-right font-semibold text-slate-700">Auth Age</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Outreach</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Phone</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {carriers.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-slate-400">
                  No carriers found
                </td>
              </tr>
            )}
            {carriers.map((c) => (
              <tr
                key={c.id}
                className="cursor-pointer hover:bg-slate-50"
                onClick={() => router.push(`/carriers/${c.id}`)}
              >
                <td className="px-4 py-3">
                  <span className="font-semibold text-slate-900">{c.legal_name}</span>
                  {c.dba_name && (
                    <span className="block text-xs text-slate-400">{c.dba_name}</span>
                  )}
                </td>
                <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-slate-700">
                  {c.dot_number}
                </td>
                <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-slate-500">
                  {c.mc_number ?? "—"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                  {c.state ?? "—"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right text-slate-700">
                  {c.power_units ?? "—"}
                </td>
                <td className="max-w-[160px] truncate px-4 py-3 text-slate-500">
                  {c.cargo_types?.join(", ") ?? "—"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right text-slate-500">
                  {authorityAge(c.authority_date)}
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  <OutreachBadge status={c.outreach_status} />
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  {c.phone ? (
                    <Link
                      href={`tel:${c.phone}`}
                      onClick={(e) => e.stopPropagation()}
                      className="text-blue-600 hover:underline"
                    >
                      {formatPhone(c.phone)}
                    </Link>
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-sm text-slate-500">
        <span>
          {total.toLocaleString()} carrier{total !== 1 ? "s" : ""}
          {totalPages > 1 ? ` — page ${page} of ${totalPages}` : ""}
        </span>
        <div className="flex gap-2">
          <button
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            className="rounded border border-slate-200 px-3 py-1 text-xs hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            ← Prev
          </button>
          <button
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
            className="rounded border border-slate-200 px-3 py-1 text-xs hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
