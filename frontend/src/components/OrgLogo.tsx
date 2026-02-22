"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api-client";

const API_BASE =
  typeof window !== "undefined" && process.env.NEXT_PUBLIC_API_BACKEND
    ? `${process.env.NEXT_PUBLIC_API_BACKEND}/api/v1`
    : "/api/v1";

type OrgLogoProps = {
  organizationId: string;
  hasLogo: boolean;
  className?: string;
  alt?: string;
};

/** Fetches and displays org logo with auth. Use when logo_url is set. */
export function OrgLogo({ organizationId, hasLogo, className, alt = "Organization logo" }: OrgLogoProps) {
  const [src, setSrc] = useState<string | null>(null);
  const blobUrlRef = useRef<string | null>(null);

  useEffect(() => {
    if (!hasLogo || !organizationId) return;
    const token = api.getToken();
    if (!token) return;
    const url = `${API_BASE}/organizations/${organizationId}/logo`;
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.blob() : null))
      .then((blob) => {
        if (blob) {
          const blobUrl = URL.createObjectURL(blob);
          blobUrlRef.current = blobUrl;
          setSrc(blobUrl);
        }
      })
      .catch(() => {});
    return () => {
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current);
        blobUrlRef.current = null;
      }
    };
  }, [organizationId, hasLogo]);

  if (!hasLogo || !src) return null;
  return <img src={src} alt={alt} className={className} />;
}
