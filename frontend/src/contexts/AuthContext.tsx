"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { api } from "@/lib/api-client";

interface AuthContextValue {
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ error?: string }>;
  signup: (email: string, password: string) => Promise<{ error?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const t = api.getToken();
    setToken(t);
    setMounted(true);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const { data, error } = await api.login({ email, password });
      if (error) return { error: error.error };
      if (data) {
        api.setToken(data.access_token);
        setToken(data.access_token);
      }
      return {};
    },
    []
  );

  const signup = useCallback(
    async (email: string, password: string) => {
      const { data, error } = await api.signup({ email, password });
      if (error) return { error: error.error };
      if (data) {
        api.setToken(data.access_token);
        setToken(data.access_token);
      }
      return {};
    },
    []
  );

  const logout = useCallback(() => {
    api.setToken(null);
    setToken(null);
  }, []);

  const value: AuthContextValue = {
    token,
    isAuthenticated: !!token,
    login,
    signup,
    logout,
  };

  if (!mounted) return null;

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
