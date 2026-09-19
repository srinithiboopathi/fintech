import axios, { AxiosError } from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Response error handler helper
export const extractErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const axiosErr = error as AxiosError<{ detail?: string | any }>;
    if (axiosErr.response?.data?.detail) {
      if (typeof axiosErr.response.data.detail === "string") {
        return axiosErr.response.data.detail;
      }
      if (Array.isArray(axiosErr.response.data.detail)) {
        return axiosErr.response.data.detail
          .map((item: any) => item.msg || JSON.stringify(item))
          .join(", ");
      }
      return JSON.stringify(axiosErr.response.data.detail);
    }
    if (axiosErr.message) {
      if (axiosErr.code === "ECONNABORTED") {
        return "Request timed out. Please check backend server latency.";
      }
      if (axiosErr.message.includes("Network Error")) {
        return "Unable to connect to QUANTLAB API. Please ensure the backend server is running on port 8000.";
      }
      return axiosErr.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "An unexpected telemetry error occurred.";
};

export interface HealthCheckResponse {
  status: string;
  app_name?: string;
  environment?: string;
}

export const checkHealth = async (): Promise<HealthCheckResponse> => {
  const response = await apiClient.get<HealthCheckResponse>("/health");
  return response.data;
};
