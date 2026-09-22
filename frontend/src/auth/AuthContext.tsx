import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { authApi, clearTokens, setTokens, User } from "../api";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

let sessionBootstrap: Promise<User> | null = null;

async function restoreOrBootstrapSession(): Promise<User> {
  if (localStorage.getItem("access_token")) {
    try {
      const existingUser = await authApi.me();
      localStorage.setItem("user", JSON.stringify(existingUser));
      return existingUser;
    } catch {
      clearTokens();
    }
  }

  // DE_Portal can provide its access token before mounting Planora AI.
  // This fallback keeps the standalone workspace login-free.
  const email = import.meta.env.VITE_BOOTSTRAP_EMAIL || "manager1@planora.local";
  const password = import.meta.env.VITE_BOOTSTRAP_PASSWORD || "manager123";
  const tokens = await authApi.login(email, password);
  setTokens(tokens.access_token, tokens.refresh_token);
  const bootstrapUser = await authApi.me();
  localStorage.setItem("user", JSON.stringify(bootstrapUser));
  return bootstrapUser;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    if (!sessionBootstrap) sessionBootstrap = restoreOrBootstrapSession();
    sessionBootstrap
      .then((restoredUser) => {
        if (active) setUser(restoredUser);
      })
      .catch(() => {
        clearTokens();
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, []);

  const login = async (email: string, password: string) => {
    const tokens = await authApi.login(email, password);
    setTokens(tokens.access_token, tokens.refresh_token);
    const me = await authApi.me();
    setUser(me);
    localStorage.setItem("user", JSON.stringify(me));
  };

  const logout = () => {
    clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
