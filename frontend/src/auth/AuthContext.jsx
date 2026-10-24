import React from "react";
import { createContext, useContext, useEffect, useState } from "react";
import api from "../api/client";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authReady, setAuthReady] = useState(false);

  useEffect(() => {
    const onUnauthorized = () => { setUser(null); setAuthReady(true); };
    window.addEventListener("verifyra:unauthorized", onUnauthorized);
    const access = localStorage.getItem("verifyra_access");
    if (!access) { setLoading(false); setAuthReady(true); }
    else api.get("/auth/me/").then(({ data }) => setUser(data))
      .catch(() => setUser(null))
      .finally(() => { setLoading(false); setAuthReady(true); });
    return () => window.removeEventListener("verifyra:unauthorized", onUnauthorized);
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/token/", { email, password });
    localStorage.setItem("verifyra_access", data.access);
    localStorage.setItem("verifyra_refresh", data.refresh);
    const me = await api.get("/auth/me/");
    setUser(me.data);
    return me.data;
  };
  const register = async (payload) => api.post("/auth/register/", payload);
  const logout = async () => {
    const refresh = localStorage.getItem("verifyra_refresh");
    try { if (refresh) await api.post("/auth/logout/", { refresh }); } finally {
      localStorage.removeItem("verifyra_access");
      localStorage.removeItem("verifyra_refresh");
      setUser(null);
    }
  };
  return <AuthContext.Provider value={{ user, loading, authReady, login, register, logout }}>
    {children}
  </AuthContext.Provider>;
}