"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/lib/api-client";
import { OrgLogo } from "@/components/OrgLogo";

const navItems = [
  { href: "/dashboard", label: "Portfolio" },
  { href: "/dashboard/forecast", label: "Forecast" },
  { href: "/dashboard/properties", label: "Properties" },
  { href: "/dashboard/data", label: "Data" },
  { href: "/dashboard/engines", label: "Engines" },
  { href: "/dashboard/contribution", label: "Contribution" },
  { href: "/dashboard/billing", label: "Billing" },
  { href: "/dashboard/alerts", label: "Alerts" },
  { href: "/dashboard/settings", label: "Settings" },
  { href: "/dashboard/training", label: "Training" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, logout } = useAuth();

  const [orgs, setOrgs] = useState<Array<{ id: string; name: string; logo_url: string | null }>>([]);

  useEffect(() => {
    if (!isAuthenticated) router.push("/");
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated) {
      api.listOrganizations().then((r) => r.data && setOrgs(r.data));
    }
  }, [isAuthenticated]);

  const primaryOrg = orgs.length === 1 ? orgs[0] : orgs.find((o) => o.logo_url);

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 glass-card rounded-none border-0 border-r border-white/10 flex flex-col">
        <div className="p-6 border-b border-white/10 flex items-center gap-3">
          {primaryOrg?.logo_url ? (
            <OrgLogo
              organizationId={primaryOrg.id}
              hasLogo={true}
              className="h-8 w-auto object-contain shrink-0"
              alt={primaryOrg.name}
            />
          ) : null}
          <Link href="/dashboard" className="text-xl font-bold text-cyan-300 truncate">
            RateMaster
          </Link>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`block px-4 py-2.5 rounded-lg transition-colors ${
                pathname === item.href
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-white/10 space-y-4">
          <button
            onClick={() => {
              logout();
              router.push("/");
            }}
            className="glass-button w-full text-slate-400 hover:text-slate-200"
          >
            Sign Out
          </button>
          <a
            href="#"
            className="flex items-center justify-center gap-2 text-slate-500 hover:text-slate-400 text-xs transition-colors py-2"
          >
            <span>Powered by</span>
            <img
              src="/assets/flow.png"
              alt="Flow"
              className="h-5 w-auto object-contain"
            />
          </a>
        </div>
      </aside>
      <main className="flex-1 p-8 overflow-auto bg-slate-950 text-slate-100">
        {children}
      </main>
    </div>
  );
}
