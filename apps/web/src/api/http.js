import axios from "axios";

export function createHttpClient({ baseURL } = {}) {
  return axios.create({
    baseURL,
    timeout: 15000,
    headers: {
      "Content-Type": "application/json",
    },
  });
}

export const http = createHttpClient({
  baseURL: (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_API_BASE_URL) || "/api",
});

