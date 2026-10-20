import type { ApiErrorBody } from '@/types/api'
import { getToken, setToken } from '@/lib/auth-token'

export class ApiError extends Error {
  status: number
  code: string
  constructor(status: number, message: string, code = 'unknown_error') {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

type Query = Record<string, string | number | boolean | null | undefined>

interface RequestOptions {
  body?: unknown
  query?: Query
  signal?: AbortSignal
}

function buildUrl(path: string, query?: Query) {
  const params = new URLSearchParams()
  for (const [k, v] of Object.entries(query ?? {})) {
    if (v !== undefined && v !== null && v !== '') params.set(k, String(v))
  }
  const qs = params.toString()
  return `/api${path}${qs ? `?${qs}` : ''}`
}

function handleUnauthorized(path: string) {
  // Bad credentials on /auth/* are a normal form error, not an expired session.
  if (path.startsWith('/auth/')) return
  if (!getToken()) return
  setToken(null)
  if (!window.location.pathname.startsWith('/login')) {
    const here = window.location.pathname + window.location.search
    window.location.assign(`/login?next=${encodeURIComponent(here)}`)
  }
}

/** Sends the request and throws `ApiError` for network failures and non-2xx responses. */
async function send(method: string, path: string, opts: RequestOptions = {}): Promise<Response> {
  const headers: Record<string, string> = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (opts.body !== undefined) headers['Content-Type'] = 'application/json'

  let res: Response
  try {
    res = await fetch(buildUrl(path, opts.query), {
      method,
      headers,
      body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
      signal: opts.signal,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err
    throw new ApiError(0, 'Нет соединения с сервером', 'network_error')
  }

  if (!res.ok) {
    let body: Partial<ApiErrorBody> | null = null
    try {
      body = await res.json()
    } catch {
      /* non-JSON error */
    }
    if (res.status === 401) handleUnauthorized(path)
    const detail = typeof body?.detail === 'string' ? body.detail : res.statusText || 'Ошибка запроса'
    throw new ApiError(res.status, detail, body?.code)
  }
  return res
}

async function request<T>(method: string, path: string, opts: RequestOptions = {}): Promise<T> {
  const res = await send(method, path, opts)
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export const api = {
  get: <T>(path: string, query?: Query) => request<T>('GET', path, { query }),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, { body: body ?? {} }),
  patch: <T>(path: string, body: unknown) => request<T>('PATCH', path, { body }),
  delete: <T = void>(path: string) => request<T>('DELETE', path),
  /** POST that hands back the raw response so the caller can read a streamed body. */
  stream: (path: string, body: unknown, signal?: AbortSignal) => send('POST', path, { body, signal }),
}

export function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Что-то пошло не так'
}
