"use client";

import { useEffect, useState } from "react";

function formatRunDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}
import { api } from "@/lib/api-client";
import type { PropertyResponse } from "@/lib/api-client";

export default function EnginesPage() {
  const [properties, setProperties] = useState<PropertyResponse[]>([]);
  const [selectedPropertyId, setSelectedPropertyId] = useState("");
  const [runningJobId, setRunningJobId] = useState<string | null>(null);
  const [runs, setRuns] = useState<
    Array<{
      id: string;
      property_id: string;
      engine_type: string;
      run_id: string;
      status: string;
      confidence: number | null;
      created_at: string;
    }>
  >([]);
  const [selectedRun, setSelectedRun] = useState<{
    run_id: string;
    engine_type: string;
    property_id?: string;
    recommendations?: Array<{
      id: string;
      stay_date: string;
      suggested_bar: number | null;
      current_bar: number | null;
      delta_dollars: number | null;
      delta_pct: number | null;
      occupancy_projection?: number | null;
      occupancy_projection_low?: number | null;
      occupancy_projection_high?: number | null;
      confidence: number | null;
      why_bullets: string[] | null;
      applied: boolean;
    }>;
    calendar?: Array<{
      stay_date: string;
      floor: number | null;
      target: number | null;
      stretch: number | null;
      confidence: number | null;
    }>;
  } | null>(null);
  const [error, setError] = useState("");
  const [appliedFilter, setAppliedFilter] = useState<"all" | "applied" | "not_applied">("all");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [applying, setApplying] = useState(false);
  const [canApprove, setCanApprove] = useState(true);
  const [propertyHealth, setPropertyHealth] = useState<number | null>(null);
  const [deletingRunId, setDeletingRunId] = useState<string | null>(null);

  useEffect(() => {
    api.listProperties().then((r) => r.data && setProperties(r.data));
    loadRuns();
  }, []);

  useEffect(() => {
    const propertyId = selectedRun?.property_id ?? selectedPropertyId;
    if (!propertyId) {
      setCanApprove(true);
      setPropertyHealth(null);
      return;
    }
    const prop = properties.find((p) => p.id === propertyId);
    if (!prop) {
      setCanApprove(true);
      setPropertyHealth(null);
      return;
    }
    api.getMyRole(prop.organization_id).then((r) => {
      const role = r.data?.role;
      setCanApprove(role === "owner" || role === "full" || role === "gm");
    });
    api.healthSummary(propertyId).then((r) => {
      setPropertyHealth(r.data?.property_health ?? null);
    });
  }, [selectedPropertyId, selectedRun?.property_id, properties]);

  function loadRuns() {
    api.listEngineRuns().then((r) => r.data && setRuns(r.data));
  }

  useEffect(() => {
    if (!runningJobId) return;
    const interval = setInterval(async () => {
      const res = await api.jobStatus(runningJobId);
      if (res.data?.status === "completed") {
        setRunningJobId(null);
        loadRuns();
      }
      if (res.data?.status === "failed") {
        setRunningJobId(null);
        setError(res.data.error ?? "Job failed");
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [runningJobId]);

  async function runEngineA() {
    if (!selectedPropertyId) {
      setError("Select a property first");
      return;
    }
    setError("");
    const res = await api.triggerEngineA(selectedPropertyId);
    if (res.error) {
      setError(res.error.error);
      return;
    }
    if (res.data?.job_id) setRunningJobId(res.data.job_id);
  }

  async function runEngineB() {
    if (!selectedPropertyId) {
      setError("Select a property first");
      return;
    }
    setError("");
    const res = await api.triggerEngineB(selectedPropertyId);
    if (res.error) {
      setError(res.error.error);
      return;
    }
    if (res.data?.job_id) setRunningJobId(res.data.job_id);
  }

  async function viewRun(runId: string) {
    const res = await api.getEngineRun(runId);
    if (res.data) {
      setSelectedRun(res.data);
      setSelectedIds(new Set());
    }
  }

  async function handleDeleteRun(runId: string) {
    setDeletingRunId(runId);
    const res = await api.deleteEngineRun(runId);
    setDeletingRunId(null);
    if (res.error) {
      setError(res.error.error);
      return;
    }
    if (selectedRun?.run_id === runId) setSelectedRun(null);
    loadRuns();
  }

  async function markApplied(recId: string) {
    await api.markRecommendationApplied(recId);
    if (selectedRun) viewRun(selectedRun.run_id);
  }

  async function applySelected() {
    if (selectedIds.size === 0 || !selectedRun) return;
    setApplying(true);
    for (const id of Array.from(selectedIds)) {
      await api.markRecommendationApplied(id);
    }
    setSelectedIds(new Set());
    if (selectedRun) viewRun(selectedRun.run_id);
    setApplying(false);
  }

  const recs = selectedRun?.recommendations ?? [];
  const filteredRecs =
    appliedFilter === "all"
      ? recs
      : appliedFilter === "applied"
        ? recs.filter((r) => r.applied)
        : recs.filter((r) => !r.applied);
  const notAppliedRecs = filteredRecs.filter((r) => !r.applied);
  const allNotAppliedSelected =
    notAppliedRecs.length > 0 && notAppliedRecs.every((r) => selectedIds.has(r.id));

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-slate-100 mb-2">
          Dual Engines
        </h1>
        <p className="text-slate-400">
          Engine A (0-30 days) tactical. Engine B (31-365 days) strategic.
        </p>
        <p className="text-slate-500 text-sm mt-2 max-w-2xl">
          Engine A outputs actionable BAR recommendations for 0–30 days. Engine B outputs Floor/Target/Stretch for 31–365 days; the 31–90 day window also has an Applied column so you can track which strategic rates you used.
        </p>
      </div>

      <div className="glass-card p-4 flex flex-wrap items-end gap-4">
        <div>
          <label htmlFor="engines-property" className="block text-sm text-slate-400 mb-2">Property</label>
          <select
            id="engines-property"
            value={selectedPropertyId}
            onChange={(e) => setSelectedPropertyId(e.target.value)}
            className="glass-input max-w-xs"
          >
            <option value="">Select property</option>
            {properties.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
        {selectedPropertyId && propertyHealth != null && (
          <div className="rounded-lg bg-white/5 border border-white/10 px-4 py-2">
            <span className="text-sm text-slate-400">Data health: </span>
            <span className="text-sm font-medium text-cyan-300">{propertyHealth}%</span>
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      {runningJobId && (
        <div className="glass-card p-4 border-cyan-500/30">
          <p className="text-cyan-300">Engine run in progress...</p>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-cyan-300 mb-2">
            Engine A - Tactical (0-30 days)
          </h3>
          <ul className="text-slate-400 text-sm space-y-2 mb-6">
            <li>Suggested BAR (Conservative / Balanced / Aggressive)</li>
            <li>Occupancy + pickup projections</li>
            <li>Sellout probability + efficiency</li>
            <li>ADR / RevPAR impact</li>
            <li>Confidence + Why bullets</li>
          </ul>
          <button
            onClick={runEngineA}
            disabled={!selectedPropertyId || !!runningJobId}
            className="glass-button glass-button-primary disabled:opacity-50"
          >
            Run Engine A
          </button>
        </div>

        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-violet-300 mb-2">
            Engine B - Strategic (31-365 days)
          </h3>
          <ul className="text-slate-400 text-sm space-y-2 mb-6">
            <li>Rate calendar: Floor / Target / Stretch</li>
            <li>Occupancy + ADR forecast bands</li>
            <li>YoY curves + seasonality + events</li>
            <li>Confidence + Why bullets</li>
          </ul>
          <button
            onClick={runEngineB}
            disabled={!selectedPropertyId || !!runningJobId}
            className="glass-button disabled:opacity-50"
          >
            Run Engine B
          </button>
        </div>
      </div>

      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">
          Recent runs
        </h3>
        {runs.length === 0 ? (
          <p className="text-slate-500">No engine runs yet.</p>
        ) : (
          <ul className="space-y-2">
            {runs.map((r) => {
              const prop = properties.find((p) => p.id === r.property_id);
              const propName = prop?.name ?? "Unknown property";
              const engineLabel = r.engine_type === "engine_a" ? "Engine A" : "Engine B";
              return (
              <li
                key={r.id}
                className="flex justify-between items-center py-2 border-b border-white/5 gap-4"
              >
                <div className="min-w-0 flex-1">
                  <span className="text-slate-300">
                    {propName} – {engineLabel}
                  </span>
                  <span className="text-xs text-slate-500 ml-2">
                    {formatRunDateTime(r.created_at)}
                  </span>
                </div>
                <div className="flex gap-2 items-center shrink-0">
                  <span className="text-xs text-slate-500">
                    conf: {r.confidence ?? "-"}
                  </span>
                  <button
                    onClick={() => viewRun(r.run_id)}
                    className="text-sm text-cyan-400 hover:underline"
                  >
                    View
                  </button>
                  <button
                    onClick={() => handleDeleteRun(r.run_id)}
                    disabled={deletingRunId === r.run_id}
                    className="text-sm text-red-400 hover:text-red-300 hover:underline disabled:opacity-50"
                    title="Delete this run"
                  >
                    {deletingRunId === r.run_id ? "Deleting…" : "Delete"}
                  </button>
                </div>
              </li>
              );
            })}
          </ul>
        )}
      </div>

      {selectedRun && (
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">
            {properties.find((p) => p.id === selectedRun.property_id)?.name ?? "Unknown property"} – {selectedRun.engine_type === "engine_a" ? "Engine A" : "Engine B"}
          </h3>
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            {selectedRun.engine_type === "engine_b" && selectedRun.recommendations && selectedRun.recommendations.length > 0 ? (
              <>
                <p className="text-slate-500 text-sm mb-2">
                  Strategic recommendations (31–90 days) — apply in your PMS and mark below.
                </p>
                <div className="flex flex-wrap items-center gap-4 mb-4">
                  <label htmlFor="applied-filter-b" className="flex items-center gap-2 text-sm text-slate-400">
                    Filter:
                    <select
                      id="applied-filter-b"
                      value={appliedFilter}
                      onChange={(e) => {
                        setAppliedFilter(e.target.value as "all" | "applied" | "not_applied");
                        setSelectedIds(new Set());
                      }}
                      className="glass-input py-1.5 px-2 text-slate-200"
                    >
                      <option value="all">All</option>
                      <option value="applied">Applied</option>
                      <option value="not_applied">Not applied</option>
                    </select>
                  </label>
                  {canApprove && selectedIds.size > 0 && (
                    <button
                      onClick={applySelected}
                      disabled={applying}
                      className="glass-button glass-button-primary text-sm py-1.5 px-3"
                    >
                      {applying ? "Applying…" : `Apply selected (${selectedIds.size})`}
                    </button>
                  )}
                  {!canApprove && (
                    <span className="text-slate-500 text-sm">Analyst: view only</span>
                  )}
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10">
                      <th className="text-left py-2 text-slate-400 w-10">
                        {canApprove && notAppliedRecs.length > 0 ? (
                          <input
                            type="checkbox"
                            checked={allNotAppliedSelected}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedIds(new Set(notAppliedRecs.map((r) => r.id)));
                              } else {
                                setSelectedIds(new Set());
                              }
                            }}
                            className="rounded"
                            aria-label="Select all not applied"
                          />
                        ) : null}
                      </th>
                      <th className="text-left py-2 text-slate-400">Stay Date</th>
                      <th className="text-left py-2 text-slate-400">Target</th>
                      <th className="text-left py-2 text-slate-400">Current</th>
                      <th className="text-left py-2 text-slate-400">Delta</th>
                      <th className="text-left py-2 text-slate-400">Occupancy</th>
                      <th className="text-left py-2 text-slate-400">Confidence</th>
                      <th className="text-left py-2 text-slate-400">Applied</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRecs.map((rec, i) => (
                      <tr key={rec.id} className="border-b border-white/5">
                        <td className="py-2 w-10">
                          {rec.applied ? (
                            <span className="text-slate-600">—</span>
                          ) : canApprove ? (
                            <input
                              type="checkbox"
                              checked={selectedIds.has(rec.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedIds((s) => {
                                    const next = new Set(s);
                                    next.add(rec.id);
                                    return next;
                                  });
                                } else {
                                  setSelectedIds((s) => {
                                    const next = new Set(s);
                                    next.delete(rec.id);
                                    return next;
                                  });
                                }
                              }}
                              className="rounded"
                              aria-label={`Select ${rec.stay_date}`}
                            />
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                        <td className="py-2 text-slate-300">{rec.stay_date}</td>
                        <td className="py-2 text-violet-300">
                          {rec.suggested_bar != null ? `$${rec.suggested_bar}` : "-"}
                        </td>
                        <td className="py-2 text-slate-400">
                          {rec.current_bar != null ? `$${rec.current_bar}` : "-"}
                        </td>
                        <td className="py-2 text-emerald-300">
                          {rec.delta_dollars != null
                            ? (rec.delta_dollars >= 0 ? `+$${rec.delta_dollars}` : `$${rec.delta_dollars}`)
                            : "-"}
                        </td>
                        <td className="py-2 text-slate-400">
                          {rec.occupancy_projection_low != null && rec.occupancy_projection_high != null
                            ? `${rec.occupancy_projection_low}–${rec.occupancy_projection_high}%`
                            : rec.occupancy_projection != null
                              ? `${rec.occupancy_projection}%`
                              : "-"}
                        </td>
                        <td className="py-2 text-slate-400">
                          {rec.confidence ?? "-"}
                        </td>
                        <td className="py-2">
                          {rec.applied ? (
                            <span className="text-emerald-400">Yes</span>
                          ) : canApprove ? (
                            <button
                              onClick={() => markApplied(rec.id)}
                              className="text-cyan-400 hover:underline"
                            >
                              Mark applied
                            </button>
                          ) : (
                            <span className="text-slate-500">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {selectedRun.calendar && selectedRun.calendar.length > 0 && (
                  <details className="mt-6">
                    <summary className="text-sm text-slate-400 cursor-pointer hover:text-slate-300">
                      Full calendar (31–365 days) — {selectedRun.calendar.length} dates
                    </summary>
                    <table className="w-full text-sm mt-2">
                      <thead>
                        <tr className="border-b border-white/10">
                          <th className="text-left py-2 text-slate-400">Stay Date</th>
                          <th className="text-left py-2 text-slate-400">Floor</th>
                          <th className="text-left py-2 text-slate-400">Target</th>
                          <th className="text-left py-2 text-slate-400">Stretch</th>
                          <th className="text-left py-2 text-slate-400">Confidence</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedRun.calendar.map((c, i) => (
                          <tr key={i} className="border-b border-white/5">
                            <td className="py-2 text-slate-300">{c.stay_date}</td>
                            <td className="py-2 text-slate-400">
                              {c.floor != null ? `$${c.floor.toFixed(0)}` : "-"}
                            </td>
                            <td className="py-2 text-violet-300">
                              {c.target != null ? `$${c.target.toFixed(0)}` : "-"}
                            </td>
                            <td className="py-2 text-cyan-300">
                              {c.stretch != null ? `$${c.stretch.toFixed(0)}` : "-"}
                            </td>
                            <td className="py-2 text-slate-400">{c.confidence ?? "-"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </details>
                )}
              </>
            ) : selectedRun.engine_type === "engine_b" && selectedRun.calendar ? (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10 sticky top-0 bg-slate-900/95">
                    <th className="text-left py-2 text-slate-400">Stay Date</th>
                    <th className="text-left py-2 text-slate-400">Floor</th>
                    <th className="text-left py-2 text-slate-400">Target</th>
                    <th className="text-left py-2 text-slate-400">Stretch</th>
                    <th className="text-left py-2 text-slate-400">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedRun.calendar.map((c, i) => (
                    <tr key={i} className="border-b border-white/5">
                      <td className="py-2 text-slate-300">{c.stay_date}</td>
                      <td className="py-2 text-slate-400">
                        {c.floor != null ? `$${c.floor.toFixed(0)}` : "-"}
                      </td>
                      <td className="py-2 text-violet-300">
                        {c.target != null ? `$${c.target.toFixed(0)}` : "-"}
                      </td>
                      <td className="py-2 text-cyan-300">
                        {c.stretch != null ? `$${c.stretch.toFixed(0)}` : "-"}
                      </td>
                      <td className="py-2 text-slate-400">{c.confidence ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <>
                <div className="flex flex-wrap items-center gap-4 mb-4">
                  <label htmlFor="applied-filter" className="flex items-center gap-2 text-sm text-slate-400">
                    Filter:
                    <select
                      id="applied-filter"
                      value={appliedFilter}
                      onChange={(e) => {
                        setAppliedFilter(e.target.value as "all" | "applied" | "not_applied");
                        setSelectedIds(new Set());
                      }}
                      className="glass-input py-1.5 px-2 text-slate-200"
                    >
                      <option value="all">All</option>
                      <option value="applied">Applied</option>
                      <option value="not_applied">Not applied</option>
                    </select>
                  </label>
                  {canApprove && selectedIds.size > 0 && (
                    <button
                      onClick={applySelected}
                      disabled={applying}
                      className="glass-button glass-button-primary text-sm py-1.5 px-3"
                    >
                      {applying ? "Applying…" : `Apply selected (${selectedIds.size})`}
                    </button>
                  )}
                  {!canApprove && (
                    <span className="text-slate-500 text-sm">Analyst: view only</span>
                  )}
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10">
                      <th className="text-left py-2 text-slate-400 w-10">
                        {canApprove && notAppliedRecs.length > 0 ? (
                          <input
                            type="checkbox"
                            checked={allNotAppliedSelected}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedIds(new Set(notAppliedRecs.map((r) => r.id)));
                              } else {
                                setSelectedIds(new Set());
                              }
                            }}
                            className="rounded"
                            aria-label="Select all not applied"
                          />
                        ) : null}
                      </th>
                      <th className="text-left py-2 text-slate-400">Stay Date</th>
                      <th className="text-left py-2 text-slate-400">Suggested BAR</th>
                      <th className="text-left py-2 text-slate-400">Current</th>
                      <th className="text-left py-2 text-slate-400">Delta</th>
                      <th className="text-left py-2 text-slate-400">Occupancy</th>
                      <th className="text-left py-2 text-slate-400">Confidence</th>
                      <th className="text-left py-2 text-slate-400">Applied</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRecs.map((rec, i) => (
                      <tr key={rec.id} className="border-b border-white/5">
                        <td className="py-2 w-10">
                          {rec.applied ? (
                            <span className="text-slate-600">—</span>
                          ) : canApprove ? (
                            <input
                              type="checkbox"
                              checked={selectedIds.has(rec.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedIds((s) => {
                                    const next = new Set(s);
                                    next.add(rec.id);
                                    return next;
                                  });
                                } else {
                                  setSelectedIds((s) => {
                                    const next = new Set(s);
                                    next.delete(rec.id);
                                    return next;
                                  });
                                }
                              }}
                              className="rounded"
                              aria-label={`Select ${rec.stay_date}`}
                            />
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                        <td className="py-2 text-slate-300">{rec.stay_date}</td>
                        <td className="py-2 text-cyan-300">
                          {rec.suggested_bar != null ? `$${rec.suggested_bar}` : "-"}
                        </td>
                        <td className="py-2 text-slate-400">
                          {rec.current_bar != null ? `$${rec.current_bar}` : "-"}
                        </td>
                        <td className="py-2 text-emerald-300">
                          {rec.delta_dollars != null
                            ? `+$${rec.delta_dollars}`
                            : "-"}
                        </td>
                        <td className="py-2 text-slate-400">
                          {rec.occupancy_projection_low != null && rec.occupancy_projection_high != null
                            ? `${rec.occupancy_projection_low}–${rec.occupancy_projection_high}%`
                            : rec.occupancy_projection != null
                              ? `${rec.occupancy_projection}%`
                              : "-"}
                        </td>
                        <td className="py-2 text-slate-400">
                          {rec.confidence ?? "-"}
                        </td>
                        <td className="py-2">
                          {rec.applied ? (
                            <span className="text-emerald-400">Yes</span>
                          ) : canApprove ? (
                            <button
                              onClick={() => markApplied(rec.id)}
                              className="text-cyan-400 hover:underline"
                            >
                              Mark applied
                            </button>
                          ) : (
                            <span className="text-slate-500">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </div>
          {selectedRun.engine_type === "engine_a" && selectedRun.recommendations?.[0]?.why_bullets && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <h4 className="text-sm font-medium text-slate-400 mb-2">
                Why drivers
              </h4>
              <ul className="text-sm text-slate-300 space-y-1">
                {selectedRun.recommendations[0].why_bullets.map((b, i) => (
                  <li key={i}>{b}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
