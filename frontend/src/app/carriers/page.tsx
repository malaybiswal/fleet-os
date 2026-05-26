"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { CarrierFilters, DEFAULT_FILTERS } from "@/components/carriers/CarrierFilters";
import type { CarrierFilterState } from "@/components/carriers/CarrierFilters";
import { CarrierKpiCards } from "@/components/carriers/CarrierKpiCards";
import { CarrierSearchBox } from "@/components/carriers/CarrierSearchBox";
import { CarriersTable } from "@/components/tables/CarriersTable";
import {
  getCarrierPipelineStats,
  listCarriers,
  listTags,
  searchCarriers,
} from "@/lib/api";
import type { CarrierListItem, CarrierPipelineStats, Paginated, Tag } from "@/types";

export default function CarriersPage() {
  const { isAuthenticated, isLoading } = useAuth();

  const [stats, setStats] = useState<CarrierPipelineStats | null>(null);
  const [result, setResult] = useState<Paginated<CarrierListItem> | null>(null);
  const [tags, setTags] = useState<Tag[]>([]);
  const [filters, setFilters] = useState<CarrierFilterState>(DEFAULT_FILTERS);
  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(1);
  const [loadingTable, setLoadingTable] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load stats + tags once
  useEffect(() => {
    if (isLoading || !isAuthenticated) return;
    Promise.all([getCarrierPipelineStats(), listTags()]).then(([s, t]) => {
      setStats(s);
      setTags(t);
    });
  }, [isAuthenticated, isLoading]);

  // Load table data whenever search / filters / page changes
  useEffect(() => {
    if (isLoading || !isAuthenticated) return;
    setLoadingTable(true);
    setError(null);

    const isSearch = searchQuery.trim().length >= 2;
    const promise = isSearch
      ? searchCarriers(searchQuery.trim(), page)
      : listCarriers({
          state: filters.state || undefined,
          authority_status: filters.authority_status || undefined,
          power_units_min: filters.power_units_min ? Number(filters.power_units_min) : undefined,
          power_units_max: filters.power_units_max ? Number(filters.power_units_max) : undefined,
          authority_age_days: filters.authority_age_days
            ? Number(filters.authority_age_days)
            : undefined,
          outreach_status: filters.outreach_status || undefined,
          tag: filters.tag || undefined,
          cargo_type: filters.cargo_type || undefined,
          order_by: filters.order_by || undefined,
          page,
          page_size: 50,
        });

    promise
      .then(setResult)
      .catch(() => setError("Failed to load carriers"))
      .finally(() => setLoadingTable(false));
  }, [isAuthenticated, isLoading, searchQuery, filters, page]);

  function handleFiltersChange(next: CarrierFilterState) {
    setFilters(next);
    setPage(1);
  }

  function handleSearch(q: string) {
    setSearchQuery(q);
    setPage(1);
  }

  if (isLoading) {
    return <div className="p-6 text-slate-500">Loading…</div>;
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Carriers</h1>
        <p className="text-slate-500">Find, evaluate, and contact carrier leads</p>
      </div>

      {stats && <CarrierKpiCards stats={stats} />}

      <CarrierSearchBox value={searchQuery} onChange={handleSearch} />

      {!searchQuery && (
        <CarrierFilters filters={filters} onChange={handleFiltersChange} tags={tags} />
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <CarriersTable
          carriers={loadingTable ? [] : result.data}
          total={result.total}
          page={result.page}
          totalPages={result.total_pages}
          onPageChange={setPage}
        />
      )}

      {loadingTable && !result && (
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-12 text-center text-sm text-slate-400 shadow-sm">
          Loading carriers…
        </div>
      )}
    </div>
  );
}
