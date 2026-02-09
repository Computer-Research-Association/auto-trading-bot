const BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);

  if (!res.ok) {
    throw new Error(`API Error ${res.status}`);
  }

  return res.json() as Promise<T>;
}
