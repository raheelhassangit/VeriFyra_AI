import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1",
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("verifyra_access");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing = false;
let waiting = [];
const settle = (error, token = null) => {
  waiting.forEach(({ resolve, reject }) => error ? reject(error) : resolve(token));
  waiting = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status !== 401 || original?._retry ||
        original?.url?.includes("/auth/token/") || original?.url?.includes("/auth/register/")) {
      return Promise.reject(error);
    }
    const refresh = localStorage.getItem("verifyra_refresh");
    if (!refresh) return Promise.reject(error);
    if (refreshing) {
      try {
        const token = await new Promise((resolve, reject) => waiting.push({ resolve, reject }));
        original.headers.Authorization = `Bearer ${token}`;
        return api(original);
      } catch (e) { return Promise.reject(e); }
    }
    original._retry = true;
    refreshing = true;
    try {
      const { data } = await axios.post(
        `${api.defaults.baseURL}/auth/token/refresh/`, { refresh }, { timeout: 15000 }
      );
      localStorage.setItem("verifyra_access", data.access);
      if (data.refresh) localStorage.setItem("verifyra_refresh", data.refresh);
      settle(null, data.access);
      original.headers.Authorization = `Bearer ${data.access}`;
      return api(original);
    } catch (refreshError) {
      settle(refreshError);
      localStorage.removeItem("verifyra_access");
      localStorage.removeItem("verifyra_refresh");
      window.dispatchEvent(new Event("verifyra:unauthorized"));
      return Promise.reject(refreshError);
    } finally { refreshing = false; }
  }
);

export const getErrorMessage = (error) => {
  const data = error?.response?.data;
  if (!data) return error?.message || "Something went wrong. Check that the API is running.";
  if (typeof data.detail === "string") return data.detail;
  return Object.entries(data).map(([key, value]) =>
    `${key}: ${Array.isArray(value) ? value.join(", ") : typeof value === "object" ? JSON.stringify(value) : value}`
  ).join(" · ");
};
export default api;