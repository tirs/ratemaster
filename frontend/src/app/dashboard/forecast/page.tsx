"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import type { PropertyResponse } from "@/lib/api-client";

type Horizon = {
  days: number;
  occupancy_avg: number;
  adr_avg: number;
  revpar_avg: number;
  pickup_avg: number;
  date_count: number;
};

export default function ForecastPage() {
  const [properties, setProperties] = useState<PropertyResponse[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [horizons, setHorizons] = useState<Horizon[]>([]);
  const [propertyCount, setPropertyCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [propertyHealth, setPropertyHealth] = useState<number | null>(null);

  useEffect(() => {
    api.listProperties().then((r) => r.data && setProperties(r.data || []));
  }, []);

  useEffect(() => {
    setLoading(true);
    api
      .forecastDashboard(selectedId || undefined)
      .then((r) => {
        if (r.data) {
          setHorizons(r.data.horizons || []);
          setPropertyCount(r.data.property_count || 0);
        } else {
          setHorizons([]);
          setPropertyCount(0);
        }
      })
      .finally(() => setLoading(false));
  }, [selectedId]);

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-slate-100 mb-2">
          Forecast Dashboard
        </h1>
        <p className="text-slate-400">
          30/60/90 day occupancy, ADR, RevPAR, and pickup forecasts from engine
          outputs.
        </p>
      </div>

      <div className="glass-card p-4 flex flex-wrap items-end gap-4">
        <div>
          <label
            htmlFor="forecast-property"
            className="block text-sm text-slate-400 mb-2"
          >
            Property
          </label>
          <select
            id="forecast-property"
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
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
        {selectedId && propertyHealth != null && (
          <div className="rounded-lg bg-white/5 border border-white/10 px-4 py-2">
            <span className="text-sm text-slate-400">Data health: </span>
            <span className="text-sm font-medium text-cyan-300">{propertyHealth}%</span>
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <p className="text-slate-400">Loading forecast…</p>
        </div>
      ) : horizons.length > 0 ? (
        <div className="glass-card p-6">
          <h2 className="text-xl font-semibold text-slate-100 mb-4">
            30/60/90 Forecast
          </h2>
          <p className="text-sm text-slate-500 mb-6">
            Aggregated from Engine A (0–30d) and Engine B (31–90d) outputs.
            {propertyCount > 0 && (
              <span className="ml-1">
                ({propertyCount} propert{propertyCount === 1 ? "y" : "ies"})
              </span>
            )}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {horizons.map((h) => (
              <div
                key={h.days}
                className="rounded-xl border border-white/10 bg-white/5 p-6 space-y-4"
              >
                <h3 className="text-lg font-semibold text-cyan-300">
                  {h.days}-day horizon
                </h3>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-xs text-slate-500 uppercase tracking-wider">
                      Occupancy
                    </dt>
                    <dd className="text-2xl font-bold text-slate-100">
                      {h.occupancy_avg.toFixed(1)}%
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500 uppercase tracking-wider">
                      ADR
                    </dt>
                    <dd className="text-2xl font-bold text-slate-100">
                      ${h.adr_avg.toFixed(2)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500 uppercase tracking-wider">
                      RevPAR
                    </dt>
                    <dd className="text-2xl font-bold text-slate-100">
                      ${h.revpar_avg.toFixed(2)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500 uppercase tracking-wider">
                      Pickup
                    </dt>
                    <dd className="text-2xl font-bold text-slate-100">
                      {h.pickup_avg.toFixed(1)}%
                    </dd>
                  </div>
                </dl>
                <p className="text-xs text-slate-500">
                  {h.date_count} dates in horizon
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="glass-card p-8 text-center">
          <p className="text-slate-400">
            No forecast data yet. Run Engine A and Engine B to generate
            forecasts.
          </p>
        </div>
      )}
    </div>
  );
}
