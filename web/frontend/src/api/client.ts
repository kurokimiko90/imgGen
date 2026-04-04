const BASE = ''

export async function apiFetch<T = Record<string, unknown>>(
  path: string,
  options?: RequestInit,
): Promise<T & { ok: boolean }> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail ?? body.error ?? `HTTP ${res.status}`)
  }

  return res.json()
}

export async function apiPost<T = Record<string, unknown>>(
  path: string,
  body: unknown,
): Promise<T & { ok: boolean }> {
  return apiFetch<T>(path, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}
