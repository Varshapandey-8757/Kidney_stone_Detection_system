import { createContext, useCallback, useContext, useEffect, useState } from "react";
import api, { refreshSession, setAccessToken } from "../api/client.js";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On page load, try to restore the session from the refresh cookie.
  useEffect(() => {
    refreshSession()
      .then((data) => setUser(data.user))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
    const expired = () => setUser(null);
    window.addEventListener("auth:expired", expired);
    return () => window.removeEventListener("auth:expired", expired);
  }, []);

  const handleAuth = (data) => {
    setAccessToken(data.access_token);
    setUser(data.user);
  };

  const login = useCallback(async (email, password) => {
    handleAuth((await api.post("/auth/login", { email, password })).data);
  }, []);

  const register = useCallback(async (name, email, password) => {
    handleAuth((await api.post("/auth/register", { name, email, password })).data);
  }, []);

  const logout = useCallback(async () => {
    try { await api.post("/auth/logout"); } finally {
      setAccessToken(null);
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
