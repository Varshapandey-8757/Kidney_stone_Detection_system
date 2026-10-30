import axios from "axios";

// Access token lives only in memory (not localStorage) so XSS can't read it from storage.
// The refresh token is an HttpOnly cookie the browser sends automatically.
let accessToken = null;
export const setAccessToken = (t) => { accessToken = t; };

const api = axios.create({ baseURL: "/api", withCredentials: true });

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});

let refreshing = null; // one refresh at a time, shared by parallel requests

export async function refreshSession() {
  if (!refreshing) {
    refreshing = axios
      .post("/api/auth/refresh", null, { withCredentials: true })
      .then((r) => { setAccessToken(r.data.access_token); return r.data; })
      .finally(() => { refreshing = null; });
  }
  return refreshing;
}

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const { config, response } = error;
    const isAuthCall = config?.url?.startsWith("/auth/");
    if (response?.status === 401 && !config._retried && !isAuthCall) {
      config._retried = true;
      try {
        await refreshSession();
        return api(config);
      } catch {
        setAccessToken(null);
        window.dispatchEvent(new Event("auth:expired"));
      }
    }
    return Promise.reject(error);
  }
);

export function errorMessage(err, fallback = "Something went wrong. Please try again.") {
  const d = err?.response?.data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d) && d[0]?.msg) return d[0].msg.replace(/^Value error, /, "");
  if (err?.response?.status === 429) return "Too many attempts. Please wait a minute and try again.";
  return fallback;
}

export default api;