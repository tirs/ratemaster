/**
 * API client - types from OpenAPI (npm run generate:api).
 * Implementation uses fetch; types are the single source of truth from backend schema.
 */

import type { components } from "./api-client.generated";

const API_BASE =
  typeof window !== "undefined"
    ? process.env.NEXT_PUBLIC_API_BACKEND
      ? `${process.env.NEXT_PUBLIC_API_BACKEND}/api/v1`
      : "/api/v1"
    : process.env.NEXT_PUBLIC_API_URL ||
      `${process.env.NEXT_PUBLIC_API_BACKEND || "http://localhost:30080"}/api/v1`;

export interface ErrorEnvelope {
  success: false;
  error: string;
  error_code?: string;
  detail?: Array<{ loc: string[]; msg: string; type: string }>;
}

export type TokenResponse = components["schemas"]["TokenResponse"];
export type OrganizationResponse = components["schemas"]["OrganizationResponse"];
export type PropertyResponse = components["schemas"]["PropertyResponse"];
export type DataSnapshotResponse = components["schemas"]["DataSnapshotResponse"];
export type OrganizationCreate = components["schemas"]["OrganizationCreate"];
export type PropertyCreate = components["schemas"]["PropertyCreate"];

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== "undefined") {
      if (token) localStorage.setItem("ratemaster_token", token);
      else localStorage.removeItem("ratemaster_token");
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== "undefined") return localStorage.getItem("ratemaster_token");
    return null;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<{ data?: T; error?: ErrorEnvelope }> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };
    const token = this.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    let res: Response;
    try {
      res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Network error";
      return { error: { success: false, error: `Connection failed: ${msg}. Is the backend running?`, error_code: "network_error" } };
    }

    const text = await res.text();
    const json = (() => {
      try {
        return text ? JSON.parse(text) : {};
      } catch {
        return {};
      }
    })();

    if (!res.ok) {
      const fallback =
        res.status === 502 || res.status === 504
          ? "Backend unreachable. Is it running?"
          : res.status === 404
            ? "Not found. Check API route and backend."
            : `Request failed (${res.status})`;
      const msg =
        json.error ||
        (typeof json.detail === "string"
          ? json.detail
          : Array.isArray(json.detail) && json.detail[0]?.msg
            ? json.detail[0].msg
            : fallback);
      return {
        error: {
          success: false,
          error: msg,
          error_code: json.error_code,
          detail: json.detail,
        },
      };
    }

    return { data: json as T };
  }

  async signup(body: { email: string; password: string }) {
    return this.request<TokenResponse>("/auth/signup", { method: "POST", body: JSON.stringify(body) });
  }

  async login(body: { email: string; password: string }) {
    return this.request<TokenResponse>("/auth/login", { method: "POST", body: JSON.stringify(body) });
  }

  async createOrganization(body: OrganizationCreate) {
    return this.request<OrganizationResponse>("/organizations", { method: "POST", body: JSON.stringify(body) });
  }

  async listOrganizations() {
    return this.request<OrganizationResponse[]>("/organizations");
  }

  async uploadOrganizationLogo(
    organizationId: string,
    file: File
  ): Promise<{ data?: OrganizationResponse; error?: ErrorEnvelope }> {
    const form = new FormData();
    form.append("file", file);
    const headers: Record<string, string> = {};
    const token = this.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/organizations/${organizationId}/logo`, {
      method: "POST",
      headers,
      body: form,
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      const errMsg =
        json.error ||
        (typeof json.detail === "string" ? json.detail : "Upload failed");
      return { error: { success: false, error: errMsg, error_code: json.error_code } };
    }
    return { data: json as OrganizationResponse };
  }

  async deleteOrganizationLogo(organizationId: string) {
    return this.request<void>(`/organizations/${organizationId}/logo`, { method: "DELETE" });
  }

  organizationLogoUrl(organizationId: string): string {
    const base =
      typeof window !== "undefined" && process.env.NEXT_PUBLIC_API_BACKEND
        ? `${process.env.NEXT_PUBLIC_API_BACKEND}/api/v1`
        : "/api/v1";
    return `${base}/organizations/${organizationId}/logo`;
  }

  async listOrgMembers(organizationId: string) {
    return this.request<Array<{ id: string; user_id: string; email: string; role: string }>>(
      `/organizations/members?organization_id=${encodeURIComponent(organizationId)}`
    );
  }

  async inviteMember(organizationId: string, email: string, role: "full" | "gm" | "analyst") {
    return this.request<{ invited: boolean; role: string }>("/organizations/members", {
      method: "POST",
      body: JSON.stringify({ organization_id: organizationId, email, role }),
    });
  }

  async removeMember(memberId: string) {
    return this.request<{ removed: boolean }>(`/organizations/members/${memberId}`, { method: "DELETE" });
  }

  async updateMemberRole(memberId: string, role: "full" | "gm" | "analyst") {
    return this.request<{ updated: boolean; role: string }>(`/organizations/members/${memberId}/role`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    });
  }

  async getMyRole(organizationId: string) {
    return this.request<{ role: string }>(`/organizations/my-role?organization_id=${encodeURIComponent(organizationId)}`);
  }

  async createProperty(body: PropertyCreate) {
    return this.request<PropertyResponse>("/organizations/properties", { method: "POST", body: JSON.stringify(body) });
  }

  async listProperties(organizationId?: string) {
    const qs = organizationId ? `?organization_id=${encodeURIComponent(organizationId)}` : "";
    return this.request<PropertyResponse[]>(`/organizations/properties${qs}`);
  }

  async listSnapshots(propertyId?: string) {
    const qs = propertyId ? `?property_id=${encodeURIComponent(propertyId)}` : "";
    return this.request<DataSnapshotResponse[]>(`/data/snapshots${qs}`);
  }

  async deleteSnapshot(snapshotId: string) {
    return this.request<never>(`/data/snapshots/${encodeURIComponent(snapshotId)}`, {
      method: "DELETE",
    });
  }

  async triggerEngineA(propertyId: string) {
    return this.request<{ job_id: string; celery_task_id: string; status: string; message: string }>("/jobs/engine-a", {
      method: "POST",
      body: JSON.stringify({ property_id: propertyId }),
    });
  }

  async triggerEngineB(propertyId: string) {
    return this.request<{ job_id: string; celery_task_id: string; status: string; message: string }>("/jobs/engine-b", {
      method: "POST",
      body: JSON.stringify({ property_id: propertyId }),
    });
  }

  async jobStatus(jobId: string) {
    return this.request<{
      job_id: string;
      status: string;
      progress?: Record<string, unknown>;
      result?: unknown;
      error?: string;
    }>(`/jobs/status/${jobId}`);
  }

  async listEngineRuns(propertyId?: string, engineType?: string) {
    const params = new URLSearchParams();
    if (propertyId) params.set("property_id", propertyId);
    if (engineType) params.set("engine_type", engineType);
    const qs = params.toString() ? `?${params}` : "";
    return this.request<
      Array<{
        id: string;
        property_id: string;
        engine_type: string;
        run_id: string;
        status: string;
        confidence: number | null;
        created_at: string;
      }>
    >(`/engines/runs${qs}`);
  }

  async deleteEngineRun(runId: string) {
    return this.request<void>(`/engines/runs/${runId}`, { method: "DELETE" });
  }

  async getEngineRun(runId: string) {
    return this.request<{
      id: string;
      run_id: string;
      engine_type: string;
      recommendations: Array<{
        id: string;
        stay_date: string;
        suggested_bar: number | null;
        current_bar: number | null;
        delta_dollars: number | null;
        delta_pct: number | null;
        confidence: number | null;
        why_bullets: string[] | null;
        applied: boolean;
      }>;
    }>(`/engines/runs/${runId}`);
  }

  async markRecommendationApplied(recId: string) {
    return this.request<{ applied: boolean }>(`/engines/recommendations/${recId}/apply`, { method: "POST" });
  }

  async contributionSummary(propertyId?: string, horizonDays = 90) {
    const params = new URLSearchParams();
    if (propertyId) params.set("property_id", propertyId);
    params.set("horizon_days", String(horizonDays));
    return this.request<{
      projected_lift_30d: number;
      projected_lift_60d: number;
      projected_lift_90d: number;
      realized_lift_mtd: number;
      realized_from_actuals: boolean;
      recommendations_in_horizon: number;
      applied_count: number;
      estimated_gop_lift: number;
      flow_through_pct: number;
    }>(`/contribution/summary?${params}`);
  }

  async topWins(propertyId?: string, limit = 10) {
    const params = new URLSearchParams();
    if (propertyId) params.set("property_id", propertyId);
    params.set("limit", String(limit));
    return this.request<
      Array<{
        stay_date: string;
        delta_dollars: number;
        suggested_bar: number;
        applied: boolean;
      }>
    >(`/contribution/top-wins?${params}`);
  }

  async avoidedLosses(propertyId?: string, limit = 10) {
    const params = new URLSearchParams();
    if (propertyId) params.set("property_id", propertyId);
    params.set("limit", String(limit));
    return this.request<
      Array<{
        stay_date: string;
        delta_dollars: number;
        suggested_bar: number;
        current_bar: number;
      }>
    >(`/contribution/avoided-losses?${params}`);
  }

  getExportUrl(path: string, params?: Record<string, string>) {
    const qs = params ? `?${new URLSearchParams(params)}` : "";
    return `${API_BASE}${path}${qs}`;
  }

  async portfolioOutlook() {
    return this.request<{ outlook: Array<{ horizon_days: number; projected_lift: number }> }>("/portfolio/outlook");
  }

  async portfolioValueRollup() {
    return this.request<{ realized_lift: number; projected_lift: number }>("/portfolio/value-rollup");
  }

  async portfolioAlertsRollup(limit = 20) {
    return this.request<
      Array<{
        id: string;
        property_id: string | null;
        alert_type: string;
        severity: string;
        title: string;
        acknowledged: boolean;
        created_at: string;
      }>
    >(`/portfolio/alerts-rollup?limit=${limit}`);
  }

  async forecastDashboard(propertyId?: string) {
    const qs = propertyId ? `?property_id=${encodeURIComponent(propertyId)}` : "";
    return this.request<{
      horizons: Array<{
        days: number;
        occupancy_avg: number;
        adr_avg: number;
        revpar_avg: number;
        pickup_avg: number;
        date_count: number;
      }>;
      property_count: number;
    }>(`/portfolio/forecast${qs}`);
  }

  async listAlerts(propertyId?: string, acknowledged?: boolean) {
    const params = new URLSearchParams();
    if (propertyId) params.set("property_id", propertyId);
    if (acknowledged !== undefined) params.set("acknowledged", String(acknowledged));
    const qs = params.toString() ? `?${params}` : "";
    return this.request<
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
    >(`/alerts${qs}`);
  }

  async getPropertySettings(propertyId: string) {
    return this.request<{
      flow_through_pct: number;
      base_monthly_fee: number;
      revenue_share_pct: number;
      revenue_share_on_gop: boolean;
      contract_effective_from: string | null;
      contract_effective_to: string | null;
      min_bar: number | null;
      max_bar: number | null;
      max_daily_change_pct: number | null;
      market_refresh_minutes: number | null;
    }>(`/properties/${propertyId}/settings`);
  }

  async getInvoice(year: number, month: number, propertyId?: string) {
    const params = new URLSearchParams({ year: String(year), month: String(month) });
    if (propertyId) params.set("property_id", propertyId);
    return this.request<{
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
    }>(`/billing/invoice?${params}`);
  }

  async yoyReport(propertyId: string) {
    return this.request<{
      property_id: string;
      trends: Array<{ year: string; total_lift: number; applied_count: number }>;
      data_trends: Array<{
        year: string;
        snapshot_type: string;
        total_revenue: number;
        row_count: number;
      }>;
    }>(`/billing/yoy?property_id=${encodeURIComponent(propertyId)}`);
  }

  async updatePropertySettings(propertyId: string, body: Record<string, unknown>) {
    return this.request(`/properties/${propertyId}/settings`, { method: "PATCH", body: JSON.stringify(body) });
  }

  async acknowledgeAlert(alertId: string) {
    return this.request<{ acknowledged: boolean }>(`/alerts/${alertId}/acknowledge`, { method: "POST" });
  }

  async healthSummary(propertyId?: string) {
    const qs = propertyId ? `?property_id=${encodeURIComponent(propertyId)}` : "";
    return this.request<{
      properties_with_data: number;
      average_health_score: number | null;
      property_health: number | null;
    }>(`/data/health-summary${qs}`);
  }

  async importPreview(file: File) {
    const form = new FormData();
    form.append("file", file);
    const headers: Record<string, string> = {};
    const token = this.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/data/import/preview`, { method: "POST", headers, body: form });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      return { error: { success: false, error: json.error || "Preview failed", error_code: json.error_code } };
    }
    return { data: json as { headers: string[]; detected_mapping: Record<string, string>; logical_fields: string[] } };
  }

  async importData(
    propertyId: string,
    file: File,
    snapshotType: "current" | "prior_year" = "current",
    columnMapping?: Record<string, string>,
    snapshotDate?: string
  ): Promise<{ data?: DataSnapshotResponse; error?: ErrorEnvelope }> {
    const form = new FormData();
    form.append("property_id", propertyId);
    form.append("snapshot_type", snapshotType);
    form.append("file", file);
    if (columnMapping && Object.keys(columnMapping).length > 0) {
      form.append("column_mapping", JSON.stringify(columnMapping));
    }
    if (snapshotDate) form.append("snapshot_date", snapshotDate);

    const headers: Record<string, string> = {};
    const token = this.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}/data/import`, { method: "POST", headers, body: form });
    const json = await res.json().catch(() => ({}));

    if (!res.ok) {
      const errMsg =
        json.error ||
        (typeof json.detail === "string"
          ? json.detail
          : Array.isArray(json.detail) && json.detail[0]?.msg
            ? json.detail[0].msg
            : "Import failed");
      return {
        error: {
          success: false,
          error: errMsg,
          error_code: json.error_code,
          detail: json.detail,
        },
      };
    }

    return { data: json as DataSnapshotResponse };
  }
}

export const api = new ApiClient();
