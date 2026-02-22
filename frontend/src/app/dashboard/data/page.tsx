"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import type { PropertyResponse } from "@/lib/api-client";

export default function DataPage() {
  const [dragOver, setDragOver] = useState(false);
  const [properties, setProperties] = useState<PropertyResponse[]>([]);
  const [selectedPropertyId, setSelectedPropertyId] = useState("");
  const [uploading, setUploading] = useState(false);
  const [lastResult, setLastResult] = useState<{
    row_count: number;
    data_health_score: number | null;
  } | null>(null);
  const [lastResultPriorYear, setLastResultPriorYear] = useState<{
    row_count: number;
    data_health_score: number | null;
  } | null>(null);
  const [error, setError] = useState("");
  const [snapshots, setSnapshots] = useState<
    Array<{
      id: string;
      property_id: string;
      snapshot_type: string;
      row_count: number;
      data_health_score: number | null;
      created_at: string;
    }>
  >([]);
  const [healthSummary, setHealthSummary] = useState<{
    properties_with_data: number;
    average_health_score: number | null;
  } | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  function loadData() {
    api.listProperties().then((r) => r.data && setProperties(r.data));
    api.listSnapshots().then((r) => r.data && setSnapshots(r.data));
    api.healthSummary().then((r) => r.data && setHealthSummary(r.data));
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleFilePriorYear(file: File) {
    if (!selectedPropertyId) {
      setError("Select a property first");
      return;
    }
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("CSV file required");
      return;
    }
    setError("");
    setUploading(true);
    const res = await api.importData(selectedPropertyId, file, "prior_year");
    setUploading(false);
    if (res.error) {
      setError(res.error.error);
      return;
    }
    if (res.data) {
      setLastResultPriorYear({
        row_count: res.data.row_count,
        data_health_score: res.data.data_health_score,
      });
      setLastResult(null);
      loadData();
    }
  }

  async function handleFile(file: File) {
    if (!selectedPropertyId) {
      setError("Select a property first");
      return;
    }
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("CSV file required");
      return;
    }
    setError("");
    setUploading(true);
    const res = await api.importData(selectedPropertyId, file, "current");
    setUploading(false);
    if (res.error) {
      setError(res.error.error);
      return;
    }
    if (res.data) {
      setLastResult({
        row_count: res.data.row_count,
        data_health_score: res.data.data_health_score,
      });
      setLastResultPriorYear(null);
      loadData();
    }
  }

  async function handleDeleteSnapshot(snapshotId: string) {
    if (!confirm("Delete this upload? This cannot be undone.")) return;
    setDeletingId(snapshotId);
    const res = await api.deleteSnapshot(snapshotId);
    setDeletingId(null);
    if (res.error) {
      setError(res.error.error);
      return;
    }
    setError("");
    loadData();
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-slate-100 mb-2">
          Data Ingestion
        </h1>
        <p className="text-slate-400">
          CSV upload with column mapping • Prior year data • Data health score
        </p>
        <p className="text-slate-500 text-sm mt-1">
          Sample data: run <code className="bg-slate-800 px-1 rounded">python scripts/generate_hotel_data.py</code> to create realistic hotel CSVs in <code className="bg-slate-800 px-1 rounded">fixtures/</code>.
        </p>
      </div>

      {properties.length === 0 ? (
        <div className="glass-card p-6 border-amber-500/30 bg-amber-500/5">
          <p className="text-amber-200">
            Create a property first in the{" "}
            <a href="/dashboard/properties" className="underline hover:text-amber-100">
              Properties
            </a>{" "}
            tab, then return here to upload data.
          </p>
        </div>
      ) : (
        <div className="glass-card p-4">
          <label htmlFor="property-select" className="block text-sm text-slate-400 mb-2">
            Property
          </label>
          <select
            id="property-select"
            value={selectedPropertyId}
            onChange={(e) => {
              setSelectedPropertyId(e.target.value);
              setError("");
              setLastResult(null);
              setLastResultPriorYear(null);
            }}
            className="glass-input w-full max-w-xs"
          >
            <option value="">Select property…</option>
            {properties.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {error && (
        <div className="glass-card p-4 border-red-500/30 bg-red-500/10">
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}

      {properties.length > 0 && (
      <div className="grid gap-6 md:grid-cols-2">
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-2">
            Current Data
          </h3>
          <p className="text-slate-400 text-sm mb-4">
            Upload CSV with stay_date, rooms_available, ADR, revenue, etc.
            Column mapping + validation.
          </p>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              const f = e.dataTransfer.files[0];
              if (f) handleFile(f);
            }}
            className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors ${
              dragOver
                ? "border-cyan-500/50 bg-cyan-500/5"
                : "border-white/20 hover:border-white/30"
            }`}
          >
            <p className="text-slate-400 mb-2">
              Drag & drop CSV or click to browse
            </p>
            <p className="text-xs text-slate-500">
              stay_date, rooms_available, total_rooms, rooms_sold, ADR,
              total_rate, revenue
            </p>
            <input
              type="file"
              accept=".csv"
              className="hidden"
              id="csv-upload"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
                e.target.value = "";
              }}
            />
            <label
              htmlFor="csv-upload"
              className={`glass-button glass-button-primary mt-4 inline-block cursor-pointer ${
                uploading || !selectedPropertyId ? "opacity-50 cursor-not-allowed" : ""
              }`}
            >
              {uploading ? "Uploading…" : "Select File"}
            </label>
          </div>
          {lastResult && (
            <div className="mt-4 flex gap-4">
              <span className="text-sm text-slate-400">
                Rows: <strong className="text-cyan-300">{lastResult.row_count}</strong>
              </span>
              <span className="text-sm text-slate-400">
                Health: <strong className="text-emerald-300">{lastResult.data_health_score ?? "—"}</strong>
              </span>
            </div>
          )}
        </div>

        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-2">
            Prior Year (YoY)
          </h3>
          <p className="text-slate-400 text-sm mb-4">
            Upload previous year data for YoY trend curves by season, DOW, and
            lead-time.
          </p>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              const f = e.dataTransfer.files[0];
              if (f) handleFilePriorYear(f);
            }}
            className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors ${
              dragOver
                ? "border-violet-500/50 bg-violet-500/5"
                : "border-white/20 hover:border-white/30"
            }`}
          >
            <p className="text-slate-400 mb-2">
              Drag and drop prior year CSV or click to browse
            </p>
            <input
              type="file"
              accept=".csv"
              className="hidden"
              id="prior-csv-upload"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFilePriorYear(f);
                e.target.value = "";
              }}
            />
            <label
              htmlFor="prior-csv-upload"
              className={`glass-button mt-4 inline-block cursor-pointer ${
                uploading || !selectedPropertyId ? "opacity-50 cursor-not-allowed" : ""
              }`}
            >
              {uploading ? "Uploading..." : "Select File"}
            </label>
          </div>
          {lastResultPriorYear && (
            <div className="mt-4 flex gap-4">
              <span className="text-sm text-slate-400">
                Rows: <strong className="text-violet-300">{lastResultPriorYear.row_count}</strong>
              </span>
              <span className="text-sm text-slate-400">
                Health: <strong className="text-emerald-300">{lastResultPriorYear.data_health_score ?? "—"}</strong>
              </span>
            </div>
          )}
        </div>
      </div>
      )}

      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">
          Data Health
        </h3>
        <p className="text-slate-400 text-sm mb-4">
          Missing dates, gaps, outliers, suspicious values. Score per property +
          recommended fixes. Feeds confidence.
        </p>
        <div className="flex gap-4">
          <div className="glass-card-hover glass-card p-4 flex-1 text-center">
            <p className="text-3xl font-bold text-cyan-300">
              {healthSummary?.average_health_score ?? "—"}
            </p>
            <p className="text-xs text-slate-500 mt-1">Avg Health Score</p>
          </div>
          <div className="glass-card-hover glass-card p-4 flex-1 text-center">
            <p className="text-3xl font-bold text-violet-300">
              {healthSummary?.properties_with_data ?? 0}
            </p>
            <p className="text-xs text-slate-500 mt-1">Properties with data</p>
          </div>
        </div>
        {snapshots.length > 0 && (
          <div className="mt-6">
            <h4 className="text-sm font-medium text-slate-400 mb-2">
              Recent imports
            </h4>
            <ul className="space-y-2">
              {snapshots.slice(0, 10).map((s) => (
                <li
                  key={s.id}
                  className="flex justify-between items-center text-sm py-2 border-b border-white/5 gap-4"
                >
                  <span className="text-slate-300 flex-1 min-w-0">
                    {properties.find((p) => p.id === s.property_id)?.name ??
                      s.property_id}{" "}
                    ({s.snapshot_type})
                  </span>
                  <span className="text-slate-500 shrink-0">
                    {s.row_count} rows, health {s.data_health_score ?? "—"}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleDeleteSnapshot(s.id)}
                    disabled={deletingId === s.id}
                    className="text-red-400 hover:text-red-300 text-xs px-2 py-1 rounded hover:bg-red-500/10 disabled:opacity-50"
                    title="Delete this upload"
                  >
                    {deletingId === s.id ? "Deleting…" : "Delete"}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
