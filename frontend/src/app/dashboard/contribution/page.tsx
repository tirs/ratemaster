"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import type { PropertyResponse } from "@/lib/api-client";

export default function ContributionPage() {
  const [properties, setProperties] = useState<PropertyResponse[]>([]);
  const [selectedPropertyId, setSelectedPropertyId] = useState("");
  const [summary, setSummary] = useState<{
    projected_lift_30d: number;
    projected_lift_60d: number;
    projected_lift_90d: number;
    realized_lift_mtd: number;
    realized_from_actuals: boolean;
    recommendations_in_horizon: number;
    applied_count: number;
    estimated_gop_lift: number;
    flow_through_pct: number;
  } | null>(null);
  const [topWins, setTopWins] = useState<
    Array<{ stay_date: string; delta_dollars: number; suggested_bar: number; applied: boolean }>
  >([]);
  const [avoidedLosses, setAvoidedLosses] = useState<
    Array<{ stay_date: string; delta_dollars: number; suggested_bar: number; current_bar: number }>
  >([]);

  useEffect(() => {
    api.listProperties().then((r) => r.data && setProperties(r.data));
  }, []);

  useEffect(() => {
    api.contributionSummary(selectedPropertyId || undefined).then(
      (r) => r.data && setSummary(r.data)
    );
    api.topWins(selectedPropertyId || undefined).then(
      (r) => r.data && setTopWins(r.data)
    );
  }, [selectedPropertyId]);

  async function exportCsv() {
    const base = process.env.NEXT_PUBLIC_API_BACKEND || "http://localhost:30080";
    const params = new URLSearchParams();
    if (selectedPropertyId) params.set("property_id", selectedPropertyId);
    const url = `${base}/api/v1/exports/contribution.csv?${params}`;
    const token = api.getToken();
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "contribution.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  async function exportReportHtml() {
    const base = process.env.NEXT_PUBLIC_API_BACKEND || "http://localhost:30080";
    const params = new URLSearchParams();
    if (selectedPropertyId) params.set("property_id", selectedPropertyId);
    const url = `${base}/api/v1/exports/contribution.html?${params}`;
    const token = api.getToken();
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "contribution_report.html";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  async function exportReportPdf() {
    const base = process.env.NEXT_PUBLIC_API_BACKEND || "http://localhost:30080";
    const params = new URLSearchParams();
    if (selectedPropertyId) params.set("property_id", selectedPropertyId);
    const url = `${base}/api/v1/exports/contribution.pdf?${params}`;
    const token = api.getToken();
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "contribution_report.pdf";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-slate-100 mb-2">
          RateMaster Contribution
        </h1>
        <p className="text-slate-400">
          Projected vs realized incremental revenue. GOP flow-through. Top wins.
        </p>
        <p className="text-slate-500 text-sm mt-1">
          Projected Lift is cumulative (60d includes 30d, 90d includes 60d). Engine A only produces recommendations for the next 30 days, so 30d/60d/90d often match when all recs fall in that window.
        </p>
      </div>

      <div className="glass-card p-4">
        <label htmlFor="property-select" className="block text-sm text-slate-400 mb-2">Property</label>
        <select
          id="property-select"
          value={selectedPropertyId}
          onChange={(e) => setSelectedPropertyId(e.target.value)}
          className="glass-input max-w-xs"
        >
          <option value="">All properties</option>
          {properties.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-5">
        <div className="glass-card p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-1">
            Projected Lift (30d)
          </h3>
          <p className="text-3xl font-bold text-cyan-300">
            {summary != null
              ? `$${summary.projected_lift_30d.toFixed(0)}`
              : "—"}
          </p>
          <p className="text-xs text-slate-500 mt-1">next 30 days</p>
        </div>
        <div className="glass-card p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-1">
            Projected Lift (60d)
          </h3>
          <p className="text-3xl font-bold text-cyan-300">
            {summary != null
              ? `$${summary.projected_lift_60d.toFixed(0)}`
              : "—"}
          </p>
          <p className="text-xs text-slate-500 mt-1">next 60 days (cumulative)</p>
        </div>
        <div className="glass-card p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-1">
            Projected Lift (90d)
          </h3>
          <p className="text-3xl font-bold text-cyan-300">
            {summary != null
              ? `$${summary.projected_lift_90d.toFixed(0)}`
              : "—"}
          </p>
          <p className="text-xs text-slate-500 mt-1">next 90 days (cumulative)</p>
        </div>
        <div className="glass-card p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-1">
            Realized MTD
          </h3>
          <p className="text-3xl font-bold text-emerald-300">
            {summary != null
              ? `$${summary.realized_lift_mtd.toFixed(0)}`
              : "—"}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            {summary?.realized_from_actuals ? "from imported actuals" : "applied recommendations"}
          </p>
        </div>
        <div className="glass-card p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-1">
            Est. GOP Lift
          </h3>
          <p className="text-3xl font-bold text-violet-300">
            {summary != null
              ? `$${summary.estimated_gop_lift.toFixed(0)}`
              : "—"}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            {summary?.flow_through_pct ?? 70}% flow-through
          </p>
        </div>
      </div>

      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">
          Applied vs Not Applied
        </h3>
        <p className="text-slate-400 text-sm mb-4">
          {summary?.applied_count ?? 0} applied of{" "}
          {summary?.recommendations_in_horizon ?? 0} in horizon.
        </p>
      </div>

      {avoidedLosses.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">
            Avoided losses
          </h3>
          <p className="text-slate-400 text-sm mb-4">
            Recommendations not applied that would have lowered revenue.
          </p>
          <ul className="space-y-2">
            {avoidedLosses.map((w, i) => (
              <li
                key={i}
                className="flex justify-between py-2 border-b border-white/5"
              >
                <span className="text-slate-300">{w.stay_date}</span>
                <span className="text-amber-300">
                  ${w.delta_dollars.toFixed(0)}
                </span>
                <span className="text-slate-500">
                  suggested ${w.suggested_bar?.toFixed(0) ?? "—"} vs current ${w.current_bar?.toFixed(0) ?? "—"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {topWins.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">
            Top opportunities
          </h3>
          <ul className="space-y-2">
            {topWins.map((w, i) => (
              <li
                key={i}
                className="flex justify-between py-2 border-b border-white/5"
              >
                <span className="text-slate-300">{w.stay_date}</span>
                <span className="text-emerald-300">
                  +${w.delta_dollars.toFixed(0)}
                </span>
                <span className="text-slate-500">
                  {w.applied ? "Applied" : "Pending"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">Exports</h3>
        <div className="flex flex-wrap gap-4">
          <button onClick={exportCsv} className="glass-button">
            CSV Export
          </button>
          <button onClick={exportReportHtml} className="glass-button">
            Report (HTML)
          </button>
          <button onClick={exportReportPdf} className="glass-button">
            Report (PDF)
          </button>
        </div>
        <p className="text-xs text-slate-500 mt-2">
          Baseline methodology: historical ADR baseline.
        </p>
      </div>
    </div>
  );
}
