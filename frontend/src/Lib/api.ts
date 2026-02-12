import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

export const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling (optional but recommended)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Check if error is due to server issues (like 502)
    if (error.response) {
      console.error(`API Error: ${error.response.status} - ${error.response.data?.message || error.message}`);
    } else {
      console.error(`Network Error: ${error.message}`);
    }
    return Promise.reject(error);
  }
);

// Simplified API fetch wrapper
export async function apiFetch<T>(endpoint: string): Promise<T> {
  const response = await api.get<T>(endpoint);
  return response.data;
}
