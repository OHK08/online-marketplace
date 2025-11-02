import axios from "axios";

// --- Base URL handling ---
const env = import.meta.env.MODE; // 'development' | 'production'
let baseURL = import.meta.env.VITE_API_BASE_URL;

// Fallbacks (in case env vars aren’t injected correctly)
if (!baseURL) {
  baseURL =
    env === "development"
      ? "http://localhost:4000/api/v1"
      : "https://art-backend-529829749133.asia-south1.run.app/api/v1";
}

console.log(`[API] Using baseURL: ${baseURL}`);

// --- Axios instance ---
const apiClient = axios.create({
  baseURL,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

// --- Request interceptor (Auth) ---
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// --- Response interceptor (Error handling) ---
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user");
      if (!window.location.pathname.includes("/login")) {
        window.location.href = "/login";
      }
    }

    // Optional: log errors for debugging in dev
    if (env === "development") {
      console.error("[API Error]", error.response || error.message);
    }

    return Promise.reject(error);
  }
);

export default apiClient;
