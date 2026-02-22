"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import type { PropertyResponse } from "@/lib/api-client";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export default function BillingPage() {
  const [properties, setProperties] = useState<PropertyResponse[]>([]);
  const [selectedPropertyId, setSelectedPropertyId] = useState("");
  const [year, setYear] = useState(() => new Date().getFullYear());
  const [month, setMonth] = useState(() => new Date().getMonth() + 1);
  const [invoice, setInvoice] = useState<{
    year: number;
    month: number;
    items: Array<{
      property_id: string;
      property_name: string;
      base_fee: number;
      revenue_share_pct: number;
      revenue_share_on_gop: boolean;
      realized_lift: number;
      gop_lift: number;
      revenue_share_amount: number;
      total: number;
    }>;
    total_base_fee: number;
    total_revenue_share: number;
    grand_total: number;
  } | null>(null);
  const [yoyPropertyId, setYoyPropertyId] = useState("");
  const [yoyTrends, setYoyTrends] = useState<
    Array<{ year: string; total_lift: number; applied_count: number }>
  >([]);
  const [yoyDataTrends, setYoyDataTrends] = useState<
    Array<{ year: string; snapshot_type: string; total_revenue: number; row_count: number }>
  >([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.listProperties().then((r) => r.data && setProperties(r.data || []));
  }, []);

  useEffect(() => {
    setLoading(true);
    api
      .getInvoice(year, month, selectedPropertyId || undefined)
      .then((r) => {
        if (r.data) setInvoice(r.data);
        else setInvoice(null);
      })
      .finally(() => setLoading(false));
  }, [year, month, selectedPropertyId]);

  async function exportBillingCsv() {
    const base = process.env.NEXT_PUBLIC_API_BACKEND || "http://localhost:30080";
    const params = new URLSearchParams({ year: String(year), month: String(month) });
    if (selectedPropertyId) params.set("property_id", selectedPropertyId);
    const url = `${base}/api/v1/exports/billing.csv?${params}`;
    const token = api.getToken();
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `billing_${year}_${month.toString().padStart(2, "0")}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  async function exportBillingPdf() {
    const base = process.env.NEXT_PUBLIC_API_BACKEND || "http://localhost:30080";
    const params = new URLSearchParams({ year: String(year), month: String(month) });
    if (selectedPropertyId) params.set("property_id", selectedPropertyId);
    const url = `${base}/api/v1/exports/billing.pdf?${params}`;
    const token = api.getToken();
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `billing_report_${year}_${month.toString().padStart(2, "0")}.pdf`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  useEffect(() => {
    if (!yoyPropertyId) {
      setYoyTrends([]);
      setYoyDataTrends([]);
      return;
    }
    api.yoyReport(yoyPropertyId).then((r) => {
      if (r.data?.trends) setYoyTrends(r.data.trends);
      else setYoyTrends([]);
      if (r.data?.data_trends) setYoyDataTrends(r.data.data_trends);
      else setYoyDataTrends([]);
    });
  }, [yoyPropertyId]);

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-slate-100 mb-2">
          Billing & Invoices
        </h1>
        <p className="text-slate-400">
          Monthly invoice (base fee + revenue share). Year-over-year trends.
        </p>
      </div>

      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">
          Monthly Invoice
        </h2>
        <div className="flex flex-wrap gap-4 mb-6">
          <div>
            <label htmlFor="invoice-year" className="block text-sm text-slate-400 mb-1">
              Year
            </label>
            <select
              id="invoice-year"
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              className="glass-input"
            >
              {[year - 2, year - 1, year, year + 1].map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="invoice-month" className="block text-sm text-slate-400 mb-1">
              Month
            </label>
            <select
              id="invoice-month"
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
              className="glass-input"
            >
              {MONTHS.map((m, i) => (
                <option key={i} value={i + 1}>{m}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="invoice-property" className="block text-sm text-slate-400 mb-1">
              Property
            </label>
            <select
              id="invoice-property"
              value={selectedPropertyId}
              onChange={(e) => setSelectedPropertyId(e.target.value)}
              className="glass-input max-w-xs"
            >
              <option value="">All properties</option>
              {properties.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <p className="text-slate-400">Loading invoice…</p>
        ) : invoice && invoice.items.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left py-2 text-slate-400">Property</th>
                    <th className="text-right py-2 text-slate-400">Base fee</th>
                    <th className="text-right py-2 text-slate-400">Realized lift</th>
                    <th className="text-right py-2 text-slate-400">GOP lift</th>
                    <th className="text-right py-2 text-slate-400">Rev share %</th>
                    <th className="text-right py-2 text-slate-400">Rev share amt</th>
                    <th className="text-right py-2 text-slate-400">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {invoice.items.map((item) => (
                    <tr key={item.property_id} className="border-b border-white/5">
                      <td className="py-2 text-slate-300">{item.property_name}</td>
                      <td className="py-2 text-right text-slate-300">
                        ${item.base_fee.toFixed(2)}
                      </td>
                      <td className="py-2 text-right text-slate-300">
                        ${item.realized_lift.toFixed(0)}
                      </td>
                      <td className="py-2 text-right text-slate-300">
                        ${item.gop_lift.toFixed(0)}
                      </td>
                      <td className="py-2 text-right text-slate-400">
                        {item.revenue_share_pct}%
                        {item.revenue_share_on_gop && " (on GOP)"}
                      </td>
                      <td className="py-2 text-right text-cyan-300">
                        ${item.revenue_share_amount.toFixed(2)}
                      </td>
                      <td className="py-2 text-right font-medium text-emerald-300">
                        ${item.total.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-6 pt-4 border-t border-white/10 flex justify-end gap-8">
              <div className="text-right">
                <span className="text-slate-400">Total base fee: </span>
                <span className="text-slate-200">${invoice.total_base_fee.toFixed(2)}</span>
              </div>
              <div className="text-right">
                <span className="text-slate-400">Total revenue share: </span>
                <span className="text-cyan-300">${invoice.total_revenue_share.toFixed(2)}</span>
              </div>
              <div className="text-right">
                <span className="text-slate-400 font-medium">Grand total: </span>
                <span className="text-emerald-300 font-bold">${invoice.grand_total.toFixed(2)}</span>
              </div>
            </div>
            <p className="text-xs text-slate-500 mt-4">
              Invoice for {MONTHS[invoice.month - 1]} {invoice.year}. Realized lift from applied recommendations; GOP = realized × flow-through. Revenue share on GOP or revenue per property settings.
            </p>
          </>
        ) : (
          <p className="text-slate-500">
            No invoice data for {MONTHS[month - 1]} {year}.
          </p>
        )}
      </div>

      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">
          Year-over-Year Trends
        </h2>
        <div className="mb-4">
          <label htmlFor="yoy-property" className="block text-sm text-slate-400 mb-2">
            Property
          </label>
          <select
            id="yoy-property"
            value={yoyPropertyId}
            onChange={(e) => setYoyPropertyId(e.target.value)}
            className="glass-input max-w-xs"
          >
            <option value="">Select property</option>
            {properties.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>

        {yoyPropertyId && (
          <>
            {yoyDataTrends.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-medium text-slate-300 mb-2">
                  Uploaded data (prior year & current)
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/10">
                        <th className="text-left py-2 text-slate-400">Year</th>
                        <th className="text-left py-2 text-slate-400">Type</th>
                        <th className="text-right py-2 text-slate-400">Revenue</th>
                        <th className="text-right py-2 text-slate-400">Rows</th>
                      </tr>
                    </thead>
                    <tbody>
                      {yoyDataTrends.map((t, i) => (
                        <tr key={`${t.year}-${t.snapshot_type}-${i}`} className="border-b border-white/5">
                          <td className="py-2 text-slate-300">{t.year}</td>
                          <td className="py-2 text-slate-400">
                            {t.snapshot_type === "prior_year" ? "Prior year" : "Current"}
                          </td>
                          <td className="py-2 text-right text-emerald-300">
                            ${t.total_revenue.toFixed(0)}
                          </td>
                          <td className="py-2 text-right text-slate-400">{t.row_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {yoyTrends.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-slate-300 mb-2">
                  Applied recommendations (Engine A/B)
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/10">
                        <th className="text-left py-2 text-slate-400">Year</th>
                        <th className="text-right py-2 text-slate-400">Total lift</th>
                        <th className="text-right py-2 text-slate-400">Applied count</th>
                      </tr>
                    </thead>
                    <tbody>
                      {yoyTrends.map((t) => (
                        <tr key={t.year} className="border-b border-white/5">
                          <td className="py-2 text-slate-300">{t.year}</td>
                          <td className="py-2 text-right text-emerald-300">
                            ${t.total_lift.toFixed(0)}
                          </td>
                          <td className="py-2 text-right text-slate-400">
                            {t.applied_count}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {yoyDataTrends.length === 0 && yoyTrends.length === 0 && (
              <p className="text-slate-500">
                No YoY data. Upload prior year or current data in the Data tab, or run Engine A/B and
                apply recommendations to see trends.
              </p>
            )}
          </>
        )}

        {!yoyPropertyId && (
          <p className="text-slate-500">Select a property to view year-over-year trends.</p>
        )}
      </div>

      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">Exports</h2>
        <div className="flex flex-wrap gap-4">
          <button onClick={exportBillingCsv} className="glass-button">
            Export CSV
          </button>
          <button onClick={exportBillingPdf} className="glass-button">
            Export PDF
          </button>
        </div>
        <p className="text-xs text-slate-500 mt-2">
          Exports invoice for {MONTHS[month - 1]} {year}
          {selectedPropertyId ? " and YoY trends for selected property" : ""}.
        </p>
      </div>
    </div>
  );
}
