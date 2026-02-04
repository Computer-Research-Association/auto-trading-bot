const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

type ApiFetchOptions = RequestInit & {
  params?: Record<string, string | number | undefined>;
};

export async function apiFetch(
  endpoint: string,
  options: ApiFetchOptions = {}
) {
  const { params, headers, ...fetchOptions } = options;

  let url = `${BASE_URL}${endpoint}`;

  if (params) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        query.append(key, String(value));
      }
    });
    url += `?${query.toString()}`;
  }

  const res = await fetch(url, {
    ...fetchOptions,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`[API ERROR] ${res.status}: ${errorText}`);
  }

  return res.json();
}
