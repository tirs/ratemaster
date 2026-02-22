"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api-client";
import type {
  OrganizationResponse,
  PropertyResponse,
} from "@/lib/api-client";

export default function PropertiesPage() {
  const searchParams = useSearchParams();
  const [orgs, setOrgs] = useState<OrganizationResponse[]>([]);
  const [props, setProps] = useState<PropertyResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateOrg, setShowCreateOrg] = useState(false);
  const [showCreateProp, setShowCreateProp] = useState(false);
  const [orgName, setOrgName] = useState("");
  const [propName, setPropName] = useState("");
  const [selectedOrgId, setSelectedOrgId] = useState("");
  const [submitLoading, setSubmitLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const action = searchParams.get("action");
    if (action === "create-org") setShowCreateOrg(true);
    if (action === "create-property") setShowCreateProp(true);
  }, [searchParams]);

  useEffect(() => {
    async function load() {
      const [orgRes, propRes] = await Promise.all([
        api.listOrganizations(),
        api.listProperties(),
      ]);
      if (orgRes.data) setOrgs(orgRes.data);
      if (propRes.data) setProps(propRes.data);
      setLoading(false);
    }
    load();
  }, []);

  async function handleCreateOrg(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitLoading(true);
    const res = await api.createOrganization({ name: orgName });
    setSubmitLoading(false);
    if (res.error) {
      setError(res.error.error);
      return;
    }
    if (res.data) {
      setOrgs((prev) => [...prev, res.data!]);
      setOrgName("");
      setShowCreateOrg(false);
    }
  }

  async function handleCreateProp(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedOrgId) {
      setError("Select an organization");
      return;
    }
    setError("");
    setSubmitLoading(true);
    const res = await api.createProperty({
      name: propName,
      organization_id: selectedOrgId,
    });
    setSubmitLoading(false);
    if (res.error) {
      setError(res.error.error);
      return;
    }
    if (res.data) {
      setProps((prev) => [...prev, res.data!]);
      setPropName("");
      setSelectedOrgId("");
      setShowCreateProp(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Loading…</div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-100 mb-2">
            Properties
          </h1>
          <p className="text-slate-400">
            Manage organizations and hotel properties
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => {
              setShowCreateOrg(true);
              setShowCreateProp(false);
            }}
            className="glass-button glass-button-primary"
          >
            + Organization
          </button>
          <button
            onClick={() => {
              setShowCreateProp(true);
              setShowCreateOrg(false);
            }}
            className="glass-button"
          >
            + Property
          </button>
        </div>
      </div>

      {showCreateOrg && (
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">
            Create Organization
          </h3>
          <form onSubmit={handleCreateOrg} className="space-y-4 max-w-md">
            <input
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              placeholder="Organization name"
              className="glass-input w-full"
              required
            />
            {error && (
              <p className="text-sm text-red-400">{error}</p>
            )}
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={submitLoading}
                className="glass-button glass-button-primary"
              >
                {submitLoading ? "Creating…" : "Create"}
              </button>
              <button
                type="button"
                onClick={() => setShowCreateOrg(false)}
                className="glass-button"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {showCreateProp && (
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">
            Add Property
          </h3>
          <form onSubmit={handleCreateProp} className="space-y-4 max-w-md">
            <div>
              <label htmlFor="create-prop-org" className="block text-sm text-slate-400 mb-1.5">
                Organization
              </label>
              <select
                id="create-prop-org"
                value={selectedOrgId}
                onChange={(e) => setSelectedOrgId(e.target.value)}
                className="glass-input w-full"
                required
              >
                <option value="">Select…</option>
                {orgs.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.name}
                  </option>
                ))}
              </select>
            </div>
            <input
              type="text"
              value={propName}
              onChange={(e) => setPropName(e.target.value)}
              placeholder="Property name"
              className="glass-input w-full"
              required
            />
            {error && <p className="text-sm text-red-400">{error}</p>}
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={submitLoading}
                className="glass-button glass-button-primary"
              >
                {submitLoading ? "Adding…" : "Add"}
              </button>
              <button
                type="button"
                onClick={() => setShowCreateProp(false)}
                className="glass-button"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="glass-card overflow-hidden">
        <table className="w-full text-slate-200">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-4 px-6 text-slate-400 font-medium">
                Property
              </th>
              <th className="text-left py-4 px-6 text-slate-400 font-medium">
                Organization
              </th>
            </tr>
          </thead>
          <tbody>
            {props.length === 0 ? (
              <tr>
                <td colSpan={2} className="py-12 text-center text-slate-400">
                  No properties yet. Add one above.
                </td>
              </tr>
            ) : (
              props.map((p) => (
                <tr
                  key={p.id}
                  className="border-b border-white/5 hover:bg-white/5 transition-colors"
                >
                  <td className="py-4 px-6 text-slate-200">{p.name}</td>
                  <td className="py-4 px-6 text-slate-300">
                    {orgs.find((o) => o.id === p.organization_id)?.name ?? "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
