"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { formatPhone } from "@/lib/utils";
import {
  addTagToCarrier,
  createNote,
  createTag,
  deleteNote,
  getCarrier,
  listCarrierTags,
  listNotes,
  listTags,
  removeTagFromCarrier,
  updateNote,
  updateOutreachStatus,
} from "@/lib/api";
import type { CarrierDetail, OutreachNote, Tag } from "@/types";

const OUTREACH_OPTIONS = [
  { value: "not_contacted", label: "Not Contacted" },
  { value: "contacted", label: "Contacted" },
  { value: "follow_up", label: "Follow Up" },
  { value: "not_interested", label: "Not Interested" },
  { value: "converted", label: "Converted" },
];

const OUTREACH_STYLES: Record<string, string> = {
  not_contacted: "bg-slate-100 text-slate-600",
  contacted: "bg-blue-100 text-blue-700",
  follow_up: "bg-yellow-100 text-yellow-700",
  not_interested: "bg-red-100 text-red-600",
  converted: "bg-emerald-100 text-emerald-700",
};

function authorityAge(authorityDate: string | null): string {
  if (!authorityDate) return "—";
  const days = Math.floor((Date.now() - new Date(authorityDate).getTime()) / 86_400_000);
  if (days < 365) return `${days} days`;
  return `${(days / 365).toFixed(1)} years`;
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString();
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-slate-400">
        {title}
      </h2>
      {children}
    </section>
  );
}

export default function CarrierDetailPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const params = useParams();
  const carrierId = Number(params.id);

  const [carrier, setCarrier] = useState<CarrierDetail | null>(null);
  const [notes, setNotes] = useState<OutreachNote[]>([]);
  const [allTags, setAllTags] = useState<Tag[]>([]);
  const [carrierTags, setCarrierTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isLoading || !isAuthenticated || !carrierId) return;
    setLoading(true);
    Promise.all([
      getCarrier(carrierId),
      listNotes(carrierId),
      listTags(),
      listCarrierTags(carrierId),
    ])
      .then(([c, n, all, cTags]) => {
        setCarrier(c);
        setNotes(n);
        setAllTags(all);
        setCarrierTags(cTags);
      })
      .catch(() => setError("Failed to load carrier"))
      .finally(() => setLoading(false));
  }, [isAuthenticated, isLoading, carrierId]);

  async function handleStatusChange(e: React.ChangeEvent<HTMLSelectElement>) {
    if (!carrier) return;
    const updated = await updateOutreachStatus(carrier.id, e.target.value);
    setCarrier(updated);
  }

  async function handleAddTag(tagId: number) {
    if (!carrier) return;
    const updated = await addTagToCarrier(carrier.id, tagId);
    setCarrierTags(updated);
  }

  async function handleRemoveTag(tagId: number) {
    if (!carrier) return;
    await removeTagFromCarrier(carrier.id, tagId);
    setCarrierTags((prev) => prev.filter((t) => t.id !== tagId));
  }

  async function handleCreateTag(name: string) {
    const tag = await createTag(name);
    setAllTags((prev) => [...prev, tag]);
    if (carrier) {
      const updated = await addTagToCarrier(carrier.id, tag.id);
      setCarrierTags(updated);
    }
  }

  if (isLoading || loading) {
    return (
      <div className="space-y-4 p-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-32 animate-pulse rounded-xl bg-slate-100" />
        ))}
      </div>
    );
  }

  if (error || !carrier) {
    return (
      <div className="p-6">
        <p className="text-sm text-red-600">{error ?? "Carrier not found"}</p>
        <Link href="/carriers" className="mt-2 inline-block text-sm text-blue-600 hover:underline">
          ← Back to Carriers
        </Link>
      </div>
    );
  }

  const availableTags = allTags.filter((t) => !carrierTags.some((ct) => ct.id === t.id));

  return (
    <div className="space-y-5">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Link href="/carriers" className="hover:text-slate-800 hover:underline">
          Carriers
        </Link>
        <span>/</span>
        <span className="text-slate-800">{carrier.legal_name}</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">{carrier.legal_name}</h1>
        {carrier.dba_name && (
          <p className="text-slate-500">DBA: {carrier.dba_name}</p>
        )}
        <p className="mt-0.5 font-mono text-sm text-slate-400">
          DOT {carrier.dot_number}
          {carrier.mc_number ? ` · MC ${carrier.mc_number}` : ""}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* Contact */}
        <Section title="Contact">
          <dl className="space-y-2 text-sm">
            <div className="flex gap-3">
              <dt className="w-24 flex-shrink-0 text-slate-500">Phone</dt>
              <dd>
                {carrier.phone ? (
                  <a href={`tel:${carrier.phone}`} className="text-blue-600 hover:underline">
                    {formatPhone(carrier.phone)}
                  </a>
                ) : "—"}
              </dd>
            </div>
            <div className="flex gap-3">
              <dt className="w-24 flex-shrink-0 text-slate-500">Email</dt>
              <dd>
                {carrier.email ? (
                  <a href={`mailto:${carrier.email}`} className="text-blue-600 hover:underline">
                    {carrier.email}
                  </a>
                ) : "—"}
              </dd>
            </div>
            <div className="flex gap-3">
              <dt className="w-24 flex-shrink-0 text-slate-500">Address</dt>
              <dd className="text-slate-700">
                {[carrier.address_line1, carrier.city, carrier.state, carrier.postal_code]
                  .filter(Boolean)
                  .join(", ") || "—"}
              </dd>
            </div>
          </dl>
        </Section>

        {/* Fleet */}
        <Section title="Fleet">
          <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <div>
              <dt className="text-slate-500">Power Units</dt>
              <dd className="font-semibold text-slate-800">{carrier.power_units ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Drivers</dt>
              <dd className="font-semibold text-slate-800">{carrier.driver_count ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Lead Score</dt>
              <dd className="font-semibold text-slate-800">{carrier.lead_score ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Authority Status</dt>
              <dd className="capitalize text-slate-700">{carrier.authority_status ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Authority Age</dt>
              <dd className="text-slate-700">{authorityAge(carrier.authority_date)}</dd>
            </div>
            <div className="col-span-2">
              <dt className="text-slate-500">Cargo Types</dt>
              <dd className="text-slate-700">{carrier.cargo_types?.join(", ") || "—"}</dd>
            </div>
          </dl>
        </Section>

        {/* Outreach */}
        <Section title="Outreach">
          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-500">Status</label>
              <select
                value={carrier.outreach_status}
                onChange={handleStatusChange}
                className={`rounded-md border px-3 py-1.5 text-sm font-medium focus:outline-none focus:ring-1 focus:ring-blue-400 ${
                  OUTREACH_STYLES[carrier.outreach_status] ?? "border-slate-200"
                }`}
              >
                {OUTREACH_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-2 block text-xs font-medium text-slate-500">Tags</label>
              <div className="flex flex-wrap gap-2">
                {carrierTags.map((t) => (
                  <span
                    key={t.id}
                    className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700"
                  >
                    {t.display_name ?? t.name}
                    <button
                      onClick={() => handleRemoveTag(t.id)}
                      className="ml-0.5 text-blue-400 hover:text-blue-600"
                      aria-label={`Remove ${t.name}`}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              {availableTags.length > 0 && (
                <select
                  className="mt-2 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
                  onChange={(e) => {
                    if (e.target.value) handleAddTag(Number(e.target.value));
                    e.target.value = "";
                  }}
                  defaultValue=""
                >
                  <option value="" disabled>Add tag…</option>
                  {availableTags.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.display_name ?? t.name}
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>
        </Section>

        {/* Notes */}
        <Section title="Notes">
          <NoteForm
            carrierId={carrier.id}
            onCreated={(n) => setNotes((prev) => [n, ...prev])}
          />
          {notes.length > 0 && (
            <div className="mt-4 space-y-3">
              {notes.map((n) => (
                <NoteItem
                  key={n.id}
                  note={n}
                  carrierId={carrier.id}
                  onDeleted={(id) => setNotes((prev) => prev.filter((x) => x.id !== id))}
                  onUpdated={(updated) =>
                    setNotes((prev) => prev.map((x) => (x.id === updated.id ? updated : x)))
                  }
                />
              ))}
            </div>
          )}
          {notes.length === 0 && (
            <p className="mt-2 text-sm text-slate-400">No notes yet.</p>
          )}
        </Section>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Note form
// ---------------------------------------------------------------------------

function NoteForm({
  carrierId,
  onCreated,
}: {
  carrierId: number;
  onCreated: (note: OutreachNote) => void;
}) {
  const [content, setContent] = useState("");
  const [outcome, setOutcome] = useState("");
  const [followUp, setFollowUp] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) return;
    setSubmitting(true);
    try {
      const note = await createNote(carrierId, {
        content: content.trim(),
        outcome: outcome || undefined,
        follow_up_date: followUp || undefined,
      });
      onCreated(note);
      setContent("");
      setOutcome("");
      setFollowUp("");
    } finally {
      setSubmitting(false);
    }
  }

  const inputCls =
    "rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400";

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Add a note…"
        rows={3}
        className={`w-full resize-none ${inputCls}`}
      />
      <div className="flex gap-2">
        <input
          type="text"
          value={outcome}
          onChange={(e) => setOutcome(e.target.value)}
          placeholder="Outcome"
          className={`flex-1 ${inputCls}`}
        />
        <input
          type="date"
          value={followUp}
          onChange={(e) => setFollowUp(e.target.value)}
          className={inputCls}
        />
      </div>
      <button
        type="submit"
        disabled={submitting || !content.trim()}
        className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {submitting ? "Saving…" : "Save Note"}
      </button>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Note item
// ---------------------------------------------------------------------------

function NoteItem({
  note,
  carrierId,
  onDeleted,
  onUpdated,
}: {
  note: OutreachNote;
  carrierId: number;
  onDeleted: (id: number) => void;
  onUpdated: (note: OutreachNote) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [content, setContent] = useState(note.content);
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await updateNote(carrierId, note.id, { content });
      onUpdated(updated);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    await deleteNote(carrierId, note.id);
    onDeleted(note.id);
  }

  const inputCls =
    "rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400";

  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 text-sm">
      {editing ? (
        <div className="space-y-2">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={3}
            className={`w-full resize-none ${inputCls}`}
          />
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="rounded-md bg-blue-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save"}
            </button>
            <button
              onClick={() => { setEditing(false); setContent(note.content); }}
              className="rounded-md border border-slate-200 px-2.5 py-1 text-xs text-slate-500 hover:bg-slate-100"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <>
          <p className="text-slate-700">{note.content}</p>
          {note.outcome && (
            <p className="mt-1 text-xs text-slate-500">Outcome: {note.outcome}</p>
          )}
          {note.follow_up_date && (
            <p className="mt-0.5 text-xs text-slate-500">
              Follow-up: {new Date(note.follow_up_date).toLocaleDateString()}
            </p>
          )}
          <div className="mt-2 flex items-center justify-between">
            <span className="text-xs text-slate-400">
              {new Date(note.created_at).toLocaleDateString()}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setEditing(true)}
                className="text-xs text-slate-400 hover:text-slate-600"
              >
                Edit
              </button>
              <button
                onClick={handleDelete}
                className="text-xs text-red-400 hover:text-red-600"
              >
                Delete
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
