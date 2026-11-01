
const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers
    }
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  if (response.status === 204) return null;

  return response.json();
}

export const api = {
  get: (endpoint) => request(endpoint),

  post: (endpoint, data) =>
    request(endpoint, {
      method: "POST",
      body: JSON.stringify(data)
    }),

  put: (endpoint, data) =>
    request(endpoint, {
      method: "PUT",
      body: JSON.stringify(data)
    })
};

export default api;
