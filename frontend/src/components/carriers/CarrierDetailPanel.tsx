"use client";

import { useEffect, useState } from "react";
import type { CarrierDetail, OutreachNote, Tag } from "@/types";
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

// ---------------------------------------------------------------------------
// Notes section
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
  const [dispatcher, setDispatcher] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) return;
    setSaving(true);
    try {
      const note = await createNote(carrierId, {
        content: content.trim(),
        outcome: outcome || undefined,
        follow_up_date: followUp || undefined,
        dispatcher_name: dispatcher || undefined,
      });
      onCreated(note);
      setContent("");
      setOutcome("");
      setFollowUp("");
      setDispatcher("");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
      <textarea
        rows={3}
        placeholder="Note…"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        className="w-full rounded border border-slate-200 bg-white px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
      />
      <div className="grid grid-cols-2 gap-2">
        <input
          type="text"
          placeholder="Outcome"
          value={outcome}
          onChange={(e) => setOutcome(e.target.value)}
          className="rounded border border-slate-200 bg-white px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
        />
        <input
          type="text"
          placeholder="Dispatcher"
          value={dispatcher}
          onChange={(e) => setDispatcher(e.target.value)}
          className="rounded border border-slate-200 bg-white px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
        />
      </div>
      <div className="flex items-center gap-2">
        <label className="text-xs text-slate-500">Follow-up</label>
        <input
          type="datetime-local"
          value={followUp}
          onChange={(e) => setFollowUp(e.target.value)}
          className="rounded border border-slate-200 bg-white px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
        />
      </div>
      <button
        type="submit"
        disabled={saving || !content.trim()}
        className="rounded bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {saving ? "Saving…" : "Add Note"}
      </button>
    </form>
  );
}

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
  const [draft, setDraft] = useState(note.content);
  const [saving, setSaving] = useState(false);

  async function save() {
    if (!draft.trim()) return;
    setSaving(true);
    try {
      const updated = await updateNote(carrierId, note.id, { content: draft.trim() });
      onUpdated(updated);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    await deleteNote(carrierId, note.id);
    onDeleted(note.id);
  }

  return (
    <div className="group rounded-lg border border-slate-100 bg-white p-3 text-sm">
      {editing ? (
        <div className="space-y-2">
          <textarea
            rows={3}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className="w-full rounded border border-slate-200 px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
          />
          <div className="flex gap-2">
            <button
              onClick={save}
              disabled={saving}
              className="rounded bg-blue-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
            >
              Save
            </button>
            <button
              onClick={() => { setEditing(false); setDraft(note.content); }}
              className="rounded border border-slate-200 px-2.5 py-1 text-xs text-slate-500 hover:bg-slate-50"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <>
          <p className="whitespace-pre-wrap text-slate-800">{note.content}</p>
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-slate-400">
            {note.outcome && <span>Outcome: {note.outcome}</span>}
            {note.dispatcher_name && <span>By: {note.dispatcher_name}</span>}
            {note.follow_up_date && <span>Follow-up: {formatDate(note.follow_up_date)}</span>}
            <span>{formatDate(note.created_at)}</span>
          </div>
          <div className="mt-2 hidden gap-2 group-hover:flex">
            <button
              onClick={() => setEditing(true)}
              className="text-xs text-blue-600 hover:underline"
            >
              Edit
            </button>
            <button onClick={remove} className="text-xs text-red-500 hover:underline">
              Delete
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tags section
// ---------------------------------------------------------------------------

function TagsSection({
  carrierId,
  carrierTags,
  allTags,
  onTagsChange,
  onTagCreated,
}: {
  carrierId: number;
  carrierTags: Tag[];
  allTags: Tag[];
  onTagsChange: (tags: Tag[]) => void;
  onTagCreated?: (tag: Tag) => void;
}) {
  const [adding, setAdding] = useState(false);
  const [input, setInput] = useState("");

  const available = allTags.filter(
    (t) => !carrierTags.some((ct) => ct.id === t.id),
  );

  async function add(tag: Tag) {
    await addTagToCarrier(carrierId, tag.id);
    onTagsChange([...carrierTags, tag]);
    setInput("");
    setAdding(false);
  }

  async function addNew() {
    const name = input.trim().toLowerCase();
    if (!name) return;
    const tag = await createTag(name);
    await addTagToCarrier(carrierId, tag.id);
    onTagsChange([...carrierTags, tag]);
    onTagCreated?.(tag);
    setInput("");
    setAdding(false);
  }

  async function remove(tagId: number) {
    await removeTagFromCarrier(carrierId, tagId);
    onTagsChange(carrierTags.filter((t) => t.id !== tagId));
  }

  const filtered = available.filter((t) =>
    (t.display_name ?? t.name).toLowerCase().includes(input.toLowerCase()),
  );

  return (
    <div>
      <div className="flex flex-wrap gap-1.5">
        {carrierTags.map((t) => (
          <span
            key={t.id}
            className="flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700"
          >
            {t.display_name ?? t.name}
            <button
              onClick={() => remove(t.id)}
              className="ml-0.5 text-slate-400 hover:text-slate-600"
              aria-label={`Remove ${t.name}`}
            >
              ×
            </button>
          </span>
        ))}
        <button
          onClick={() => setAdding(!adding)}
          className="rounded-full border border-dashed border-slate-300 px-2.5 py-0.5 text-xs text-slate-400 hover:border-slate-400 hover:text-slate-600"
        >
          + Add tag
        </button>
      </div>
      {adding && (
        <div className="mt-2 space-y-1">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Tag name…"
            autoFocus
            className="w-full rounded border border-slate-200 px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
          />
          {filtered.length > 0 && (
            <div className="rounded border border-slate-200 bg-white shadow-sm">
              {filtered.slice(0, 8).map((t) => (
                <button
                  key={t.id}
                  onClick={() => add(t)}
                  className="block w-full px-3 py-1.5 text-left text-sm hover:bg-slate-50"
                >
                  {t.display_name ?? t.name}
                </button>
              ))}
            </div>
          )}
          {input.trim() &&
            !available.some(
              (t) => (t.display_name ?? t.name).toLowerCase() === input.trim().toLowerCase(),
            ) && (
              <button
                onClick={addNew}
                className="text-xs text-blue-600 hover:underline"
              >
                Create "{input.trim()}"
              </button>
            )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main panel
// ---------------------------------------------------------------------------

type Props = {
  carrierId: number | null;
  onClose: () => void;
  onCarrierUpdated?: (updated: CarrierDetail) => void;
  onTagCreated?: (tag: Tag) => void;
};

export function CarrierDetailPanel({ carrierId, onClose, onCarrierUpdated, onTagCreated }: Props) {
  const [carrier, setCarrier] = useState<CarrierDetail | null>(null);
  const [notes, setNotes] = useState<OutreachNote[]>([]);
  const [allTags, setAllTags] = useState<Tag[]>([]);
  const [carrierTags, setCarrierTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!carrierId) return;
    setLoading(true);
    setCarrier(null);
    setNotes([]);
    setCarrierTags([]);

    Promise.all([
      getCarrier(carrierId),
      listNotes(carrierId),
      listTags(),
      listCarrierTags(carrierId),
    ]).then(([c, n, all, cTags]) => {
      setCarrier(c);
      setNotes(n);
      setAllTags(all);
      setCarrierTags(cTags);
    }).finally(() => setLoading(false));
  }, [carrierId]);

  async function handleStatusChange(e: React.ChangeEvent<HTMLSelectElement>) {
    if (!carrier) return;
    const updated = await updateOutreachStatus(carrier.id, e.target.value);
    setCarrier(updated);
    onCarrierUpdated?.(updated);
  }

  if (!carrierId) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-30 bg-black/20"
        onClick={onClose}
      />

      {/* Panel */}
      <aside className="fixed right-0 top-0 z-40 flex h-full w-[480px] flex-col bg-white shadow-xl">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            {loading || !carrier ? (
              <div className="h-5 w-48 animate-pulse rounded bg-slate-200" />
            ) : (
              <>
                <h2 className="text-lg font-bold text-slate-900">{carrier.legal_name}</h2>
                {carrier.dba_name && (
                  <p className="text-sm text-slate-400">{carrier.dba_name}</p>
                )}
                <p className="mt-0.5 font-mono text-xs text-slate-400">
                  DOT {carrier.dot_number}
                  {carrier.mc_number ? ` · MC ${carrier.mc_number}` : ""}
                </p>
              </>
            )}
          </div>
          <button
            onClick={onClose}
            className="ml-4 mt-0.5 text-slate-400 hover:text-slate-600"
            aria-label="Close"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
          {!loading && carrier && (
            <>
              {/* Contact */}
              <section>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Contact
                </h3>
                <dl className="space-y-1 text-sm">
                  <div className="flex gap-2">
                    <dt className="w-20 flex-shrink-0 text-slate-500">Phone</dt>
                    <dd>
                      {carrier.phone ? (
                        <a href={`tel:${carrier.phone}`} className="text-blue-600 hover:underline">
                          {carrier.phone}
                        </a>
                      ) : "—"}
                    </dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="w-20 flex-shrink-0 text-slate-500">Email</dt>
                    <dd>
                      {carrier.email ? (
                        <a href={`mailto:${carrier.email}`} className="text-blue-600 hover:underline">
                          {carrier.email}
                        </a>
                      ) : "—"}
                    </dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="w-20 flex-shrink-0 text-slate-500">Address</dt>
                    <dd className="text-slate-700">
                      {[carrier.address_line1, carrier.city, carrier.state, carrier.postal_code]
                        .filter(Boolean)
                        .join(", ") || "—"}
                    </dd>
                  </div>
                </dl>
              </section>

              {/* Fleet */}
              <section>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Fleet
                </h3>
                <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                  <div className="flex gap-2">
                    <dt className="text-slate-500">Power Units</dt>
                    <dd className="font-semibold text-slate-800">{carrier.power_units ?? "—"}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-slate-500">Drivers</dt>
                    <dd className="font-semibold text-slate-800">{carrier.driver_count ?? "—"}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-slate-500">Authority</dt>
                    <dd className="capitalize text-slate-700">{carrier.authority_status ?? "—"}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-slate-500">Auth Age</dt>
                    <dd className="text-slate-700">{authorityAge(carrier.authority_date)}</dd>
                  </div>
                  <div className="col-span-2 flex gap-2">
                    <dt className="text-slate-500">Cargo</dt>
                    <dd className="text-slate-700">{carrier.cargo_types?.join(", ") || "—"}</dd>
                  </div>
                </dl>
              </section>

              {/* CRM */}
              <section>
                <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
                  CRM
                </h3>

                <div className="space-y-4">
                  {/* Status */}
                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-500">
                      Outreach Status
                    </label>
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

                  {/* Tags */}
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-slate-500">Tags</label>
                    <TagsSection
                      carrierId={carrier.id}
                      carrierTags={carrierTags}
                      allTags={allTags}
                      onTagsChange={setCarrierTags}
                      onTagCreated={(tag) => {
                        setAllTags((prev) => [...prev, tag]);
                        onTagCreated?.(tag);
                      }}
                    />
                  </div>

                  {/* Notes */}
                  <div>
                    <label className="mb-2 block text-xs font-medium text-slate-500">Notes</label>
                    <NoteForm
                      carrierId={carrier.id}
                      onCreated={(n) => setNotes((prev) => [n, ...prev])}
                    />
                    {notes.length > 0 && (
                      <div className="mt-3 space-y-2">
                        {notes.map((n) => (
                          <NoteItem
                            key={n.id}
                            note={n}
                            carrierId={carrier.id}
                            onDeleted={(id) => setNotes((prev) => prev.filter((x) => x.id !== id))}
                            onUpdated={(updated) =>
                              setNotes((prev) =>
                                prev.map((x) => (x.id === updated.id ? updated : x)),
                              )
                            }
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </section>
            </>
          )}

          {loading && (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 animate-pulse rounded-lg bg-slate-100" />
              ))}
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
