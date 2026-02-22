"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api-client";
import { OrgLogo } from "@/components/OrgLogo";
import type { PropertyResponse, OrganizationResponse } from "@/lib/api-client";

type OrgMember = { id: string; user_id: string; email: string; role: string };

export default function SettingsPage() {
  const [properties, setProperties] = useState<PropertyResponse[]>([]);
  const [organizations, setOrganizations] = useState<
    Array<OrganizationResponse & { logo_url?: string | null }>
  >([]);
  const [selectedId, setSelectedId] = useState("");
  const [selectedOrgId, setSelectedOrgId] = useState("");
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"full" | "gm" | "analyst">("full");
  const [inviteStatus, setInviteStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [inviteError, setInviteError] = useState("");
  const [myRole, setMyRole] = useState<string | null>(null);
  const [myRoleForProperty, setMyRoleForProperty] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [settings, setSettings] = useState<{
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
  } | null>(null);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [saveError, setSaveError] = useState("");
  const [logoUploading, setLogoUploading] = useState(false);
  const [logoDeleting, setLogoDeleting] = useState(false);
  const logoInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.listProperties().then((r) => r.data && setProperties(r.data));
    api.listOrganizations().then((r) => r.data && setOrganizations(r.data || []));
  }, []);

  const selectedOrg = organizations.find((o) => o.id === selectedOrgId);
  const hasLogo = !!selectedOrg?.logo_url;

  async function handleLogoUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !selectedOrgId) return;
    if (!file.type.startsWith("image/") || !["image/png", "image/jpeg", "image/webp"].includes(file.type)) {
      setInviteError("Logo must be PNG, JPG, or WebP");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      setInviteError("Logo must be under 2MB");
      return;
    }
    setLogoUploading(true);
    setInviteError("");
    const res = await api.uploadOrganizationLogo(selectedOrgId, file);
    setLogoUploading(false);
    if (res.error) {
      setInviteError(res.error.error || "Upload failed");
    } else {
      api.listOrganizations().then((r) => r.data && setOrganizations(r.data || []));
    }
    e.target.value = "";
  }

  async function handleLogoDelete() {
    if (!selectedOrgId || !confirm("Remove organization logo?")) return;
    setLogoDeleting(true);
    setInviteError("");
    const res = await api.deleteOrganizationLogo(selectedOrgId);
    setLogoDeleting(false);
    if (res.error) {
      setInviteError(res.error.error || "Delete failed");
    } else {
      api.listOrganizations().then((r) => r.data && setOrganizations(r.data || []));
    }
  }

  useEffect(() => {
    if (!selectedOrgId) {
      setMembers([]);
      setMyRole(null);
      return;
    }
    api.listOrgMembers(selectedOrgId).then((r) => r.data && setMembers(r.data));
    api.getMyRole(selectedOrgId).then((r) => setMyRole(r.data?.role ?? null));
  }, [selectedOrgId]);

  useEffect(() => {
    if (!selectedId) {
      setSettings(null);
      setSaveStatus("idle");
      setSaveError("");
      setMyRoleForProperty(null);
      return;
    }
    setSaveStatus("idle");
    setSaveError("");
    api.getPropertySettings(selectedId).then(
      (r) => r.data && setSettings(r.data)
    ).catch(() => setSettings(null));
    const prop = properties.find((p) => p.id === selectedId);
    if (prop) {
      api.getMyRole(prop.organization_id).then(
        (r) => setMyRoleForProperty(r.data?.role ?? null)
      );
    } else {
      setMyRoleForProperty(null);
    }
  }, [selectedId, properties]);

  async function inviteMember(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedOrgId || !inviteEmail.trim()) return;
    setInviteStatus("sending");
    setInviteError("");
    const res = await api.inviteMember(selectedOrgId, inviteEmail.trim(), inviteRole);
    if (res.error) {
      setInviteStatus("error");
      setInviteError(res.error.error || "Invite failed");
    } else {
      setInviteStatus("sent");
      setInviteEmail("");
      api.listOrgMembers(selectedOrgId).then((r) => r.data && setMembers(r.data));
      setTimeout(() => setInviteStatus("idle"), 3000);
    }
  }

  async function removeMember(memberId: string) {
    if (!confirm("Remove this member from the organization?")) return;
    setRemovingId(memberId);
    const res = await api.removeMember(memberId);
    setRemovingId(null);
    if (res.error) {
      setInviteError(res.error.error || "Failed to remove");
      setInviteStatus("error");
    } else if (selectedOrgId) {
      api.listOrgMembers(selectedOrgId).then((r) => r.data && setMembers(r.data));
    }
  }

  async function changeRole(memberId: string, role: "full" | "gm" | "analyst") {
    const res = await api.updateMemberRole(memberId, role);
    if (res.error) {
      setInviteError(res.error.error || "Failed to update role");
      setInviteStatus("error");
    } else if (selectedOrgId) {
      api.listOrgMembers(selectedOrgId).then((r) => r.data && setMembers(r.data));
    }
  }

  async function save() {
    if (!selectedId || !settings) return;
    setSaveStatus("saving");
    setSaveError("");
    const res = await api.updatePropertySettings(selectedId, settings);
    if (res.error) {
      setSaveStatus("error");
      const d = res.error.detail;
      const msg =
        res.error.error ||
        (typeof d === "string" ? d : Array.isArray(d) ? d.map((e: { msg?: string }) => e?.msg).filter(Boolean).join("; ") : null) ||
        "Failed to save";
      setSaveError(msg);
    } else {
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus("idle"), 3000);
    }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-slate-100 mb-2">
          Property Settings
        </h1>
        <p className="text-slate-400">
          Flow-through, billing, guardrails
        </p>
      </div>

      <div className="glass-card p-4">
        <label htmlFor="settings-property" className="block text-sm text-slate-400 mb-2">Property</label>
        <select
          id="settings-property"
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
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

      {settings && (
        <div className="glass-card p-6 space-y-4 max-w-lg">
          <div>
            <label htmlFor="flow-through-pct" className="block text-sm text-slate-400 mb-1">
              Flow-through %
            </label>
            <input
              id="flow-through-pct"
              type="number"
              value={settings.flow_through_pct}
              onChange={(e) =>
                setSettings({ ...settings, flow_through_pct: Number(e.target.value) })
              }
              className="glass-input w-full"
            />
          </div>
          <div>
            <label htmlFor="base-monthly-fee" className="block text-sm text-slate-400 mb-1">
              Base monthly fee
            </label>
            <input
              id="base-monthly-fee"
              type="number"
              value={settings.base_monthly_fee}
              onChange={(e) =>
                setSettings({ ...settings, base_monthly_fee: Number(e.target.value) })
              }
              className="glass-input w-full"
            />
          </div>
          <div>
            <label htmlFor="revenue-share-pct" className="block text-sm text-slate-400 mb-1">
              Revenue share %
            </label>
            <input
              id="revenue-share-pct"
              type="number"
              value={settings.revenue_share_pct}
              onChange={(e) =>
                setSettings({ ...settings, revenue_share_pct: Number(e.target.value) })
              }
              className="glass-input w-full"
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              id="revenue-share-on-gop"
              type="checkbox"
              checked={settings.revenue_share_on_gop}
              onChange={(e) =>
                setSettings({ ...settings, revenue_share_on_gop: e.target.checked })
              }
            />
            <label htmlFor="revenue-share-on-gop" className="text-sm text-slate-400">
              Revenue share on GOP lift
            </label>
          </div>
          <div>
            <label htmlFor="contract-effective-from" className="block text-sm text-slate-400 mb-1">
              Contract effective from
            </label>
            <input
              id="contract-effective-from"
              type="date"
              value={settings.contract_effective_from ?? ""}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  contract_effective_from: e.target.value || null,
                })
              }
              className="glass-input w-full"
              placeholder="Optional"
            />
          </div>
          <div>
            <label htmlFor="contract-effective-to" className="block text-sm text-slate-400 mb-1">
              Contract effective to
            </label>
            <input
              id="contract-effective-to"
              type="date"
              value={settings.contract_effective_to ?? ""}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  contract_effective_to: e.target.value || null,
                })
              }
              className="glass-input w-full"
              placeholder="Optional"
            />
          </div>
          <div>
            <label htmlFor="min-bar" className="block text-sm text-slate-400 mb-1">
              Min BAR (guardrail)
            </label>
            <input
              id="min-bar"
              type="number"
              value={settings.min_bar ?? ""}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  min_bar: e.target.value ? Number(e.target.value) : null,
                })
              }
              className="glass-input w-full"
              placeholder="Optional"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">
              Max BAR (guardrail)
            </label>
            <input
              type="number"
              value={settings.max_bar ?? ""}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  max_bar: e.target.value ? Number(e.target.value) : null,
                })
              }
              className="glass-input w-full"
              placeholder="Optional"
            />
          </div>
          <div>
            <label htmlFor="max-daily-change-pct" className="block text-sm text-slate-400 mb-1">
              Max daily change %
            </label>
            <input
              id="max-daily-change-pct"
              type="number"
              value={settings.max_daily_change_pct ?? ""}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  max_daily_change_pct: e.target.value
                    ? Number(e.target.value)
                    : null,
                })
              }
              className="glass-input w-full"
              placeholder="Optional"
            />
          </div>
          <div>
            <label htmlFor="market-refresh-minutes" className="block text-sm text-slate-400 mb-1">
              Market refresh cadence (min)
            </label>
            <input
              id="market-refresh-minutes"
              type="number"
              min={5}
              max={60}
              value={settings.market_refresh_minutes ?? ""}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  market_refresh_minutes: e.target.value
                    ? Number(e.target.value)
                    : null,
                })
              }
              className="glass-input w-full"
              placeholder="5–60 (uses global default if empty)"
            />
          </div>
          {!["analyst"].includes(myRoleForProperty ?? "") && (
          <button
            onClick={save}
            disabled={saveStatus === "saving"}
            className="glass-button glass-button-primary"
          >
            {saveStatus === "saving" ? "Saving…" : "Save"}
          </button>
          )}
          {myRoleForProperty === "analyst" && (
            <p className="text-sm text-slate-500">Only Owner or GM can edit settings.</p>
          )}
          {saveStatus === "saved" && (
            <p className="text-sm text-emerald-400">Settings saved successfully.</p>
          )}
          {saveStatus === "error" && (
            <p className="text-sm text-red-400">{saveError}</p>
          )}
        </div>
      )}

      <div className="glass-card p-6">
        <h2 className="text-xl font-semibold text-slate-100 mb-4">Organization Profile</h2>
        <p className="text-slate-400 text-sm mb-4">
          Upload your organization logo for a professional appearance on reports and dashboards.
        </p>
        <div className="mb-4">
          <label htmlFor="profile-org" className="block text-sm text-slate-400 mb-2">
            Organization
          </label>
          <select
            id="profile-org"
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
            className="glass-input max-w-xs"
          >
            <option value="">Select organization</option>
            {organizations.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>
        </div>
        {selectedOrgId && (myRole === "owner" || myRole === "full" || myRole === "gm") && (
          <div className="flex flex-wrap items-start gap-6">
            <div className="w-32 h-32 rounded-lg border-2 border-dashed border-white/20 flex items-center justify-center bg-white/5 overflow-hidden">
              {hasLogo ? (
                <OrgLogo
                  organizationId={selectedOrgId}
                  hasLogo={true}
                  className="w-full h-full object-contain p-2"
                  alt={selectedOrg?.name ?? "Logo"}
                />
              ) : (
                <span className="text-slate-500 text-sm text-center px-2">No logo</span>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <input
                ref={logoInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="hidden"
                onChange={handleLogoUpload}
                aria-label="Upload organization logo"
              />
              <button
                type="button"
                onClick={() => logoInputRef.current?.click()}
                disabled={logoUploading}
                className="glass-button glass-button-primary text-sm"
              >
                {logoUploading ? "Uploading…" : "Upload logo"}
              </button>
              {hasLogo && (
                <button
                  type="button"
                  onClick={handleLogoDelete}
                  disabled={logoDeleting}
                  className="text-sm text-red-400 hover:text-red-300"
                >
                  {logoDeleting ? "Removing…" : "Remove logo"}
                </button>
              )}
              <p className="text-xs text-slate-500">PNG, JPG, or WebP. Max 2MB.</p>
            </div>
          </div>
        )}
        {selectedOrgId && ["analyst"].includes(myRole ?? "") && hasLogo && (
          <div className="w-32 h-32 rounded-lg border border-white/10 flex items-center justify-center bg-white/5 overflow-hidden">
            <OrgLogo
              organizationId={selectedOrgId}
              hasLogo={true}
              className="w-full h-full object-contain p-2"
              alt={selectedOrg?.name ?? "Logo"}
            />
          </div>
        )}
      </div>

      <div className="glass-card p-6">
        <h2 className="text-xl font-semibold text-slate-100 mb-4">Team & Roles</h2>
        <p className="text-slate-400 text-sm mb-4">
          {myRole === "owner"
            ? "Invite GM or Analyst. Only owners can invite, remove, or change roles."
            : myRole
              ? "View team members. Contact the owner to change roles."
              : "Select an organization to view team."}
        </p>
        <div className="mb-4">
          <label htmlFor="team-org" className="block text-sm text-slate-400 mb-2">
            Organization
          </label>
          <select
            id="team-org"
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
            className="glass-input max-w-xs"
          >
            <option value="">Select organization</option>
            {organizations.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>
        </div>
        {selectedOrgId && (
          <>
            <div className="mb-4">
              <h3 className="text-sm font-medium text-slate-300 mb-2">Members</h3>
              <ul className="space-y-2">
                {members.map((m) => (
                  <li
                    key={m.id}
                    className="flex items-center justify-between py-2 px-3 rounded-lg bg-white/5 gap-2"
                  >
                    <span className="text-slate-200">{m.email}</span>
                    <span className="flex items-center gap-2">
                      {myRole === "owner" && m.role !== "owner" ? (
                        <>
                          <select
                            value={m.role}
                            onChange={(e) =>
                              changeRole(m.id, e.target.value as "full" | "gm" | "analyst")
                            }
                            className="glass-input text-sm py-1 px-2"
                            aria-label={`Change role for ${m.email}`}
                          >
                            <option value="full">Full user</option>
                            <option value="gm">GM</option>
                            <option value="analyst">Analyst</option>
                          </select>
                          <button
                            type="button"
                            onClick={() => removeMember(m.id)}
                            disabled={removingId === m.id}
                            className="text-red-400 hover:text-red-300 text-sm"
                          >
                            {removingId === m.id ? "…" : "Remove"}
                          </button>
                        </>
                      ) : (
                        <span className="text-sm text-cyan-400">
                          {m.role === "full" ? "Full user" : m.role === "gm" ? "GM" : m.role.charAt(0).toUpperCase() + m.role.slice(1)}
                        </span>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
            {myRole === "owner" && (
            <form onSubmit={inviteMember} className="flex flex-wrap gap-3 items-end">
              <div>
                <label htmlFor="invite-email" className="block text-sm text-slate-400 mb-1">
                  Email
                </label>
                <input
                  id="invite-email"
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="user@example.com"
                  className="glass-input w-56"
                  required
                />
              </div>
              <div>
                <label htmlFor="invite-role" className="block text-sm text-slate-400 mb-1">
                  Role
                </label>
                <select
                  id="invite-role"
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as "full" | "gm" | "analyst")}
                  className="glass-input"
                >
                  <option value="full">Full user</option>
                  <option value="gm">GM</option>
                  <option value="analyst">Analyst</option>
                </select>
              </div>
              <button
                type="submit"
                disabled={inviteStatus === "sending"}
                className="glass-button glass-button-primary"
              >
                {inviteStatus === "sending" ? "Inviting…" : "Invite"}
              </button>
            </form>
            )}
            {inviteStatus === "sent" && (
              <p className="text-sm text-emerald-400 mt-2">Invite sent successfully.</p>
            )}
            {inviteStatus === "error" && (
              <p className="text-sm text-red-400 mt-2">{inviteError}</p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
