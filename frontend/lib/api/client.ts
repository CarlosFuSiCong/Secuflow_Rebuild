import axios, { AxiosInstance } from "axios";

const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

export const apiClient: AxiosInstance = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers = config.headers ?? {};
      (config.headers as Record<string, string>).Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Flag to prevent multiple refresh requests
let isRefreshing = false;
// Queue for pending requests while refreshing
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Auth endpoints return 401 for invalid credentials — let the caller handle it
    const isAuthEndpoint = originalRequest?.url?.includes("/auth/login/") ||
      originalRequest?.url?.includes("/auth/register/");

    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      if (isRefreshing) {
        // If already refreshing, add to queue
        return new Promise(function (resolve, reject) {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers["Authorization"] = "Bearer " + token;
            return apiClient(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem("refresh_token");

      if (!refreshToken) {
        // No refresh token, redirect to login
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");
          window.location.href = "/sign-in";
        }
        return Promise.reject(error);
      }

      try {
        // Call refresh endpoint using default axios (no interceptors)
        // Adjust endpoint path if needed. Based on backend/secuflow/urls.py it is /token/refresh/
        // but baseURL includes /api, so it should be /token/refresh/ relative to baseURL?
        // Wait, baseURL is http://localhost:8000/api
        // urls.py: path('api/token/refresh/', ...)
        // So if baseURL is .../api, then /token/refresh/ is correct relative to it if using apiClient,
        // but I am using axios directly.
        // Full URL: http://localhost:8000/api/token/refresh/
        
        const response = await axios.post(`${baseURL}/token/refresh/`, {
          refresh: refreshToken,
        });

        const { access } = response.data;

        localStorage.setItem("access_token", access);
        
        // Update default headers
        apiClient.defaults.headers.common["Authorization"] = "Bearer " + access;
        originalRequest.headers["Authorization"] = "Bearer " + access;

        processQueue(null, access);

        return apiClient(originalRequest);
      } catch (err) {
        processQueue(err, null);
        
        // If refresh fails, clear everything and redirect
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          localStorage.removeItem("user");
          window.location.href = "/sign-in";
        }
        
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
