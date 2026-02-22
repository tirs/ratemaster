"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import type { PropertyResponse } from "@/lib/api-client";

export default function AlertsPage() {
  const [properties, setProperties] = useState<PropertyResponse[]>([]);
  const [selectedPropertyId, setSelectedPropertyId] = useState("");
  const [alerts, setAlerts] = useState<
    Array<{
      id: string;
      property_id: string | null;
      alert_type: string;
      severity: string;
      title: string;
      message: string | null;
      acknowledged: boolean;
      created_at: string;
    }>
  >([]);

  useEffect(() => {
    api.listProperties().then((r) => r.data && setProperties(r.data || []));
  }, []);

  useEffect(() => {
    api
      .listAlerts(selectedPropertyId || undefined)
      .then((r) => r.data && setAlerts(r.data));
  }, [selectedPropertyId]);

  async function acknowledge(id: string) {
    await api.acknowledgeAlert(id);
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, acknowledged: true } : a))
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-slate-100 mb-2">
          Alerts and Task Inbox
        </h1>
        <p className="text-slate-400">
          Sellout risk, market undercutting, pickup deviation, confidence issues
        </p>
      </div>

      <div className="glass-card p-4">
        <label htmlFor="alerts-property" className="block text-sm text-slate-400 mb-2">
          Property
        </label>
        <select
          id="alerts-property"
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

      <div className="glass-card p-6">
        {alerts.length === 0 ? (
          <p className="text-slate-500">No alerts.</p>
        ) : (
          <ul className="space-y-3">
            {alerts.map((a) => (
              <li
                key={a.id}
                className={`flex justify-between items-center py-3 border-b border-white/5 ${
                  a.acknowledged ? "opacity-60" : ""
                }`}
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        a.severity === "high"
                          ? "bg-red-500/20 text-red-300"
                          : a.severity === "med"
                          ? "bg-amber-500/20 text-amber-300"
                          : "bg-slate-500/20 text-slate-400"
                      }`}
                    >
                      {a.severity}
                    </span>
                    <span className="text-slate-300">{a.title}</span>
                    {!selectedPropertyId && a.property_id && (
                      <span className="text-xs text-slate-500">
                        ({properties.find((p) => p.id === a.property_id)?.name ?? a.property_id})
                      </span>
                    )}
                  </div>
                  {a.message && (
                    <p className="text-sm text-slate-500 mt-1">{a.message}</p>
                  )}
                </div>
                {!a.acknowledged && (
                  <button
                    onClick={() => acknowledge(a.id)}
                    className="glass-button text-sm"
                  >
                    Acknowledge
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
