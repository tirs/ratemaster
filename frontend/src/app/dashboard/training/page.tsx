"use client";

import { useState } from "react";
import Link from "next/link";

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "getting-started", label: "Getting Started" },
  { id: "roles", label: "Roles" },
  { id: "properties-data", label: "Properties & Data" },
  { id: "engines", label: "Engines" },
  { id: "contribution", label: "Contribution" },
  { id: "settings", label: "Settings" },
  { id: "alerts", label: "Alerts" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function TrainingPage() {
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-slate-100 mb-2">
          RateMaster Training
        </h1>
        <p className="text-slate-400">
          Learn how to use the system end-to-end. Everything you need to get
          started.
        </p>
      </div>

      {/* Tab navigation */}
      <div className="glass-card p-2">
        <div className="flex flex-wrap gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="glass-card p-8 max-w-4xl">
        {activeTab === "overview" && <OverviewContent />}
        {activeTab === "getting-started" && <GettingStartedContent />}
        {activeTab === "roles" && <RolesContent />}
        {activeTab === "properties-data" && <PropertiesDataContent />}
        {activeTab === "engines" && <EnginesContent />}
        {activeTab === "contribution" && <ContributionContent />}
        {activeTab === "settings" && <SettingsContent />}
        {activeTab === "alerts" && <AlertsContent />}

        {/* Prev/Next navigation */}
        <nav className="flex justify-between mt-10 pt-6 border-t border-white/10">
          {TABS[TABS.findIndex((t) => t.id === activeTab) - 1] ? (
            <button
              onClick={() =>
                setActiveTab(
                  TABS[TABS.findIndex((t) => t.id === activeTab) - 1].id
                )
              }
              className="text-sm text-cyan-400 hover:underline flex items-center gap-1"
            >
              ← {TABS[TABS.findIndex((t) => t.id === activeTab) - 1].label}
            </button>
          ) : (
            <span />
          )}
          {TABS[TABS.findIndex((t) => t.id === activeTab) + 1] ? (
            <button
              onClick={() =>
                setActiveTab(
                  TABS[TABS.findIndex((t) => t.id === activeTab) + 1].id
                )
              }
              className="text-sm text-cyan-400 hover:underline flex items-center gap-1"
            >
              {TABS[TABS.findIndex((t) => t.id === activeTab) + 1].label} →
            </button>
          ) : (
            <span />
          )}
        </nav>
      </div>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-8 last:mb-0">
      <h2 className="text-lg font-semibold text-cyan-300 mb-3">{title}</h2>
      <div className="text-slate-300 space-y-3">{children}</div>
    </section>
  );
}

function Tip({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex gap-3 p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
      <span className="text-emerald-400 shrink-0">💡</span>
      <p className="text-sm text-slate-300">{children}</p>
    </div>
  );
}

function OverviewContent() {
  return (
    <div className="prose prose-invert max-w-none">
      <Section title="Quick Links">
        <div className="flex flex-wrap gap-2">
          <Link
            href="/dashboard"
            className="px-3 py-1.5 rounded-lg bg-cyan-500/20 text-cyan-300 text-sm hover:bg-cyan-500/30"
          >
            Portfolio
          </Link>
          <Link
            href="/dashboard/forecast"
            className="px-3 py-1.5 rounded-lg bg-white/10 text-slate-300 text-sm hover:bg-white/15"
          >
            Forecast
          </Link>
          <Link
            href="/dashboard/properties"
            className="px-3 py-1.5 rounded-lg bg-white/10 text-slate-300 text-sm hover:bg-white/15"
          >
            Properties
          </Link>
          <Link
            href="/dashboard/data"
            className="px-3 py-1.5 rounded-lg bg-white/10 text-slate-300 text-sm hover:bg-white/15"
          >
            Data
          </Link>
          <Link
            href="/dashboard/engines"
            className="px-3 py-1.5 rounded-lg bg-white/10 text-slate-300 text-sm hover:bg-white/15"
          >
            Engines
          </Link>
          <Link
            href="/dashboard/contribution"
            className="px-3 py-1.5 rounded-lg bg-white/10 text-slate-300 text-sm hover:bg-white/15"
          >
            Contribution
          </Link>
          <Link
            href="/dashboard/settings"
            className="px-3 py-1.5 rounded-lg bg-white/10 text-slate-300 text-sm hover:bg-white/15"
          >
            Settings
          </Link>
        </div>
      </Section>
      <Section title="What is RateMaster?">
        <p>
          RateMaster is a revenue and pricing recommendation platform for hotels.
          It uses dual engines (tactical + strategic) to suggest optimal BAR
          (Best Available Rate) and tracks the value you generate.
        </p>
      </Section>
      <Section title="Key Concepts">
        <ul className="list-disc pl-6 space-y-2">
          <li>
            <strong className="text-slate-200">Portfolio</strong> — Your
            organizations and properties rolled up
          </li>
          <li>
            <strong className="text-slate-200">Current Data</strong> — This
            period&apos;s stay dates, ADR, revenue
          </li>
          <li>
            <strong className="text-slate-200">Prior Year (YoY)</strong> — Last
            year&apos;s data for trend curves
          </li>
          <li>
            <strong className="text-slate-200">Engine A</strong> — Tactical
            (0–30 days): actionable BAR recommendations
          </li>
          <li>
            <strong className="text-slate-200">Engine B</strong> — Strategic
            (31–365 days): floor/target/stretch bands
          </li>
          <li>
            <strong className="text-slate-200">Contribution</strong> — Projected
            vs realized lift, GOP flow-through
          </li>
          <li>
            <strong className="text-slate-200">Forecast</strong> — 30/60/90 day
            occupancy, ADR, RevPAR, pickup from engine outputs
          </li>
          <li>
            <strong className="text-slate-200">Roles</strong> — Owner, Full user,
            GM, Analyst with different permissions
          </li>
        </ul>
      </Section>
      <Section title="Typical Workflow">
        <ol className="list-decimal pl-6 space-y-2">
          <li>Create an organization and add properties</li>
          <li>Upload current CSV + prior year CSV</li>
          <li>Configure property settings (flow-through, guardrails)</li>
          <li>Run Engine A and Engine B</li>
          <li>Review recommendations, mark applied when you use them</li>
          <li>View contribution dashboard and export reports</li>
        </ol>
      </Section>
    </div>
  );
}

function GettingStartedContent() {
  return (
    <div className="prose prose-invert max-w-none">
      <Section title="1. Create an Organization">
        <p>
          Go to <Link href="/dashboard/properties" className="text-cyan-400 hover:underline">Properties</Link> and create an organization (your portfolio).
          This groups your hotels.
        </p>
      </Section>
      <Section title="2. Add Properties">
        <p>
          Add one or more properties under the organization. Each property has
          its own data, engine runs, and settings.
        </p>
      </Section>
      <Section title="3. Upload Data">
        <p>
          Go to <Link href="/dashboard/data" className="text-cyan-400 hover:underline">Data</Link> and upload two CSVs per property:
        </p>
        <ul className="list-disc pl-6 space-y-1">
          <li>
            <strong>Current Data</strong> — This period (e.g. Feb 2025)
          </li>
          <li>
            <strong>Prior Year (YoY)</strong> — Same period last year (e.g. Feb
            2024)
          </li>
        </ul>
        <Tip>
          Sample CSVs are in <code className="bg-white/10 px-1.5 py-0.5 rounded text-cyan-300">sample-data/</code> in the project root.
        </Tip>
      </Section>
      <Section title="4. Run Engines">
        <p>
          Go to <Link href="/dashboard/engines" className="text-cyan-400 hover:underline">Engines</Link>, select a property, and run Engine A and Engine B.
          Celery must be running for jobs to complete.
        </p>
      </Section>
      <Section title="5. View Results">
        <p>
          Check <Link href="/dashboard" className="text-cyan-400 hover:underline">Portfolio</Link> for 30/60/90 outlook,{" "}
          <Link href="/dashboard/forecast" className="text-cyan-400 hover:underline">Forecast</Link> for occupancy/ADR/RevPAR, and{" "}
          <Link href="/dashboard/contribution" className="text-cyan-400 hover:underline">Contribution</Link> for lift metrics and exports.
        </p>
      </Section>
      <Section title="6. Invite Your Team (Owners)">
        <p>
          If you&apos;re the organization owner, go to{" "}
          <Link href="/dashboard/settings" className="text-cyan-400 hover:underline">Settings → Team &amp; Roles</Link> to invite Full users, GMs, or Analysts.
          Invitees must sign up first; then you add them by email.
        </p>
      </Section>
    </div>
  );
}

function RolesContent() {
  return (
    <div className="prose prose-invert max-w-none">
      <Section title="Role Hierarchy">
        <p>
          RateMaster has four roles: <strong>Owner</strong>, <strong>Full user</strong>,{" "}
          <strong>GM</strong>, and <strong>Analyst</strong>. Permissions differ by role.
        </p>
      </Section>
      <Section title="Permission Matrix">
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-white/20">
                <th className="text-left py-2 text-slate-400">Role</th>
                <th className="text-left py-2 text-slate-400">Approve recommendations</th>
                <th className="text-left py-2 text-slate-400">Edit settings</th>
                <th className="text-left py-2 text-slate-400">Invite / remove / change roles</th>
              </tr>
            </thead>
            <tbody className="text-slate-300">
              <tr className="border-b border-white/10">
                <td className="py-2 font-medium">Owner</td>
                <td className="py-2">Yes</td>
                <td className="py-2">Yes</td>
                <td className="py-2">Yes</td>
              </tr>
              <tr className="border-b border-white/10">
                <td className="py-2 font-medium">Full user</td>
                <td className="py-2">Yes</td>
                <td className="py-2">Yes</td>
                <td className="py-2">No</td>
              </tr>
              <tr className="border-b border-white/10">
                <td className="py-2 font-medium">GM</td>
                <td className="py-2">Yes</td>
                <td className="py-2">Yes</td>
                <td className="py-2">No</td>
              </tr>
              <tr className="border-b border-white/10">
                <td className="py-2 font-medium">Analyst</td>
                <td className="py-2">No</td>
                <td className="py-2">No</td>
                <td className="py-2">No</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Section>
      <Section title="Inviting Users">
        <p>
          Only <strong>owners</strong> can invite. Go to Settings → Team &amp; Roles, select an
          organization, enter the user&apos;s email (they must have signed up first), and
          choose Full user, GM, or Analyst.
        </p>
      </Section>
      <Section title="Analyst View-Only">
        <p>
          Analysts can view all dashboards, run engines, and upload data, but cannot
          mark recommendations as applied or edit property settings.
        </p>
      </Section>
    </div>
  );
}

function PropertiesDataContent() {
  return (
    <div className="prose prose-invert max-w-none">
      <Section title="Properties">
        <p>
          Each property belongs to an organization. You can have multiple
          properties per org. Properties are where you upload data, run engines,
          and configure settings.
        </p>
      </Section>
      <Section title="CSV Format">
        <p>Your CSV should include these columns (auto-detected):</p>
        <ul className="list-disc pl-6 space-y-1">
          <li>
            <strong>stay_date</strong> — Required. Format: YYYY-MM-DD
          </li>
          <li>
            <strong>booking_date</strong> — Optional. Enables lead-time patterns
          </li>
          <li>
            <strong>rooms_available</strong>, <strong>total_rooms</strong>,{" "}
            <strong>rooms_sold</strong>
          </li>
          <li>
            <strong>adr</strong>, <strong>total_rate</strong>,{" "}
            <strong>revenue</strong>
          </li>
        </ul>
        <p className="text-sm text-slate-500">
          Aliases like &quot;Stay Date&quot;, &quot;ADR&quot;, &quot;Revenue&quot; are
          auto-mapped.
        </p>
      </Section>
      <Section title="Data Health">
        <p>
          After upload, you get a Data Health score (0–100). Gaps, missing
          dates, and outliers lower the score. Fix recommended issues for better
          engine outputs.
        </p>
      </Section>
      <Section title="Prior Year (YoY)">
        <p>
          Upload prior year data with the same structure but dates shifted back
          one year. This powers YoY trend curves by season, day-of-week, and
          lead-time bucket.
        </p>
      </Section>
    </div>
  );
}

function EnginesContent() {
  return (
    <div className="prose prose-invert max-w-none">
      <Section title="Engine A — Tactical (0–30 days)">
        <p>
          Produces <strong>actionable BAR recommendations</strong> for the next
          30 days. Each row is a suggestion: &quot;Set BAR to $X on date Y.&quot;
        </p>
        <ul className="list-disc pl-6 space-y-1">
          <li>Conservative / Balanced / Aggressive options</li>
          <li>Delta vs current BAR</li>
          <li>Confidence and &quot;Why&quot; bullets</li>
          <li>
            <strong>Applied</strong> column — Mark when you use a recommendation
          </li>
        </ul>
        <Tip>
          Use the filter and &quot;Select all&quot; to bulk-mark recommendations as
          applied. Only Owner, Full user, and GM can approve; Analysts see view-only.
        </Tip>
      </Section>
      <Section title="Engine B — Strategic (31–365 days)">
        <p>
          Produces a <strong>rate calendar</strong> with Floor / Target /
          Stretch bands. These are planning guidelines, not per-date actions.
        </p>
        <ul className="list-disc pl-6 space-y-1">
          <li>Seasonality-based bands</li>
          <li>YoY curves + events</li>
          <li>No &quot;Applied&quot; — used for budgeting and strategy</li>
        </ul>
      </Section>
      <Section title="Running Engines">
        <p>
          Select a property, click &quot;Run Engine A&quot; or &quot;Run Engine B&quot;. Jobs run in
          the background via Celery. Ensure Celery worker is running:
        </p>
        <pre className="bg-slate-900/80 rounded-lg p-4 text-sm overflow-x-auto">
          celery -A celery_worker worker -l info --pool=solo
        </pre>
      </Section>
      <Section title="Market Snapshots &amp; Re-runs">
        <p>
          When you add a market snapshot (manual or CSV import), Engine A automatically
          re-runs for that property. The scheduled market refresh also triggers Engine A
          for properties with market data.
        </p>
      </Section>
    </div>
  );
}

function ContributionContent() {
  return (
    <div className="prose prose-invert max-w-none">
      <Section title="What is Contribution?">
        <p>
          Contribution tracks the value RateMaster generates: projected lift vs
          realized lift, and estimated GOP lift based on your flow-through
          setting.
        </p>
      </Section>
      <Section title="Metrics">
        <ul className="list-disc pl-6 space-y-1">
          <li>
            <strong>Projected Lift (30d)</strong> — Sum of delta from all
            recommendations in horizon
          </li>
          <li>
            <strong>Realized MTD</strong> — Lift from recommendations you
            marked as applied
          </li>
          <li>
            <strong>Est. GOP Lift</strong> — Projected lift × flow-through %
          </li>
        </ul>
      </Section>
      <Section title="Exports">
        <p>Three export options:</p>
        <ul className="list-disc pl-6 space-y-1">
          <li>
            <strong>CSV Export</strong> — For finance, with stay_date, suggested_bar,
            delta, applied
          </li>
          <li>
            <strong>Report (HTML)</strong> — Full report in a browser-friendly
            HTML file
          </li>
          <li>
            <strong>Report (PDF)</strong> — Printable PDF with summary, tables,
            and top opportunities
          </li>
        </ul>
      </Section>
    </div>
  );
}

function SettingsContent() {
  return (
    <div className="prose prose-invert max-w-none">
      <Section title="Property Settings">
        <p>
          Go to <Link href="/dashboard/settings" className="text-cyan-400 hover:underline">Settings</Link> and select a property to configure. Only Owner, Full user, and GM can edit; Analysts see read-only.
        </p>
      </Section>
      <Section title="Team &amp; Roles">
        <p>
          In Settings, scroll to <strong>Team &amp; Roles</strong>. Owners can invite Full users, GMs, or Analysts by email, remove members, and change roles. Invitees must sign up first.
        </p>
      </Section>
      <Section title="Flow-through %">
        <p>
          Share of revenue lift that flows to GOP. Typical: 60–80%. Used for
          estimated GOP lift in Contribution.
        </p>
      </Section>
      <Section title="Base Monthly Fee & Revenue Share">
        <p>
          Billing terms. Revenue share can be on revenue lift or GOP lift
          (toggle &quot;Revenue share on GOP lift&quot;).
        </p>
      </Section>
      <Section title="Guardrails">
        <ul className="list-disc pl-6 space-y-1">
          <li>
            <strong>Min BAR</strong> — Lowest allowed BAR (engine won&apos;t suggest
            below)
          </li>
          <li>
            <strong>Max BAR</strong> — Highest allowed BAR
          </li>
          <li>
            <strong>Max daily change %</strong> — Limit how much BAR can change
            day-over-day
          </li>
        </ul>
      </Section>
      <Section title="Contract Effective Dates">
        <p>
          Optional <strong>contract_effective_from</strong> and <strong>contract_effective_to</strong> dates
          filter which recommendations count toward billing. The invoice only includes
          realized lift for stay dates within the contract period.
        </p>
      </Section>
      <Section title="Scheduled Jobs">
        <p>
          With Celery beat running: <strong>market refresh</strong> runs periodically (configurable),
          and <strong>training jobs</strong> run daily to calibrate models from outcomes.
        </p>
      </Section>
    </div>
  );
}

function AlertsContent() {
  return (
    <div className="prose prose-invert max-w-none">
      <Section title="Alerts">
        <p>
          Go to <Link href="/dashboard/alerts" className="text-cyan-400 hover:underline">Alerts</Link> to see notifications. Engine run completions, data
          health issues, and other events appear here.
        </p>
      </Section>
      <Section title="Alert Types">
        <ul className="list-disc pl-6 space-y-1">
          <li>
            <strong>engine_run_complete</strong> — Engine A or B finished
          </li>
          <li>
            <strong>sellout_risk</strong> — High sellout probability or low efficiency
          </li>
          <li>
            <strong>market_undercutting</strong> — Suggested BAR below compset average
          </li>
          <li>
            <strong>pickup_deviation</strong> — Pickup projection outside expected range
          </li>
          <li>
            <strong>confidence_issue</strong> — Low data health score
          </li>
        </ul>
      </Section>
    </div>
  );
}
