"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api-client";
import type { OrganizationResponse, PropertyResponse } from "@/lib/api-client";

export default function DashboardPage() {
  const [orgs, setOrgs] = useState<OrganizationResponse[]>([]);
  const [props, setProps] = useState<PropertyResponse[]>([]);
  const [outlook, setOutlook] = useState<Array<{ horizon_days: number; projected_lift: number }>>([]);
  const [valueRollup, setValueRollup] = useState<{ realized_lift: number; projected_lift: number } | null>(null);
  const [alertsRollup, setAlertsRollup] = useState<
    Array<{ id: string; acknowledged: boolean; severity: string; title: string }>
  >([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const [orgRes, propRes, outlookRes, valueRes, alertsRes] = await Promise.all([
        api.listOrganizations(),
        api.listProperties(),
        api.portfolioOutlook(),
        api.portfolioValueRollup(),
        api.portfolioAlertsRollup(),
      ]);
      if (orgRes.data) setOrgs(orgRes.data);
      if (propRes.data) setProps(propRes.data);
      if (outlookRes.data?.outlook) setOutlook(outlookRes.data.outlook);
      if (valueRes.data) setValueRollup(valueRes.data);
      if (alertsRes.data) setAlertsRollup(alertsRes.data);
      setLoading(false);
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Loading portfolio…</div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-slate-100 mb-2">
          Portfolio Dashboard
        </h1>
        <p className="text-slate-400">
          Rollups across properties. Next 30/60/90 outlook. Alerts. Value generated.
        </p>
      </div>

      {outlook.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">
            30/60/90 Outlook
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {outlook.map((o) => (
              <div
                key={o.horizon_days}
                className="flex flex-col items-center justify-center p-4 rounded-lg bg-white/5 border border-white/10"
              >
                <p className="text-sm font-medium text-slate-400 mb-1">
                  {o.horizon_days}d projected
                </p>
                <p className="text-2xl font-bold text-cyan-300">
                  ${o.projected_lift.toFixed(0)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="glass-card glass-card-hover p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-1">
            Organizations
          </h3>
          <p className="text-3xl font-bold text-cyan-300">{orgs.length}</p>
          <Link
            href="/dashboard/properties?action=create-org"
            className="mt-3 inline-block text-sm text-cyan-400 hover:underline"
          >
            + Create organization
          </Link>
        </div>
        <div className="glass-card glass-card-hover p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-1">
            Properties
          </h3>
          <p className="text-3xl font-bold text-violet-300">{props.length}</p>
          <Link
            href="/dashboard/properties?action=create-property"
            className="mt-3 inline-block text-sm text-violet-400 hover:underline"
          >
            + Add property
          </Link>
        </div>
        <div className="glass-card glass-card-hover p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-1">
            RateMaster Value
          </h3>
          <p className="text-3xl font-bold text-emerald-300">
            {valueRollup != null ? `$${valueRollup.realized_lift.toFixed(0)}` : "—"}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Realized lift (applied)
          </p>
        </div>
        <Link href="/dashboard/alerts" className="glass-card glass-card-hover p-6 block">
          <h3 className="text-sm font-medium text-slate-400 mb-1">
            Alerts
          </h3>
          <p className="text-3xl font-bold text-amber-300">
            {alertsRollup.filter((a) => !a.acknowledged).length}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            unacknowledged
          </p>
          <span className="mt-3 inline-block text-sm text-amber-400 hover:underline">
            View all alerts →
          </span>
        </Link>
      </div>

      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">
          Organizations
        </h2>
        {orgs.length === 0 ? (
          <p className="text-slate-500">
            No organizations yet. Create one to get started.
          </p>
        ) : (
          <ul className="space-y-3">
            {orgs.map((org) => (
              <li
                key={org.id}
                className="flex items-center justify-between py-2 border-b border-white/5 last:border-0"
              >
                <span className="text-slate-200">{org.name}</span>
                <span className="text-xs text-slate-500">
                  {props.filter((p) => p.organization_id === org.id).length}{" "}
                  properties
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
