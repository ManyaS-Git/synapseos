/**
 * Type-safe API client for communicating with the SynapseOS backend.
 *
 * Features:
 * - Environment-aware base URL
 * - Configurable request timeout
 * - Structured error handling
 * - Request/response type safety
 */

const DEFAULT_TIMEOUT_MS = 10_000;

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly statusText: string,
    public readonly body: unknown,
    public readonly endpoint: string,
  ) {
    super(`API Error ${status} ${statusText} on ${endpoint}`);
    this.name = 'ApiError';
  }
}

export class ApiTimeoutError extends Error {
  constructor(
    public readonly endpoint: string,
    public readonly timeoutMs: number,
  ) {
    super(`Request to ${endpoint} timed out after ${timeoutMs}ms`);
    this.name = 'ApiTimeoutError';
  }
}

interface RequestOptions extends Omit<RequestInit, 'method' | 'body'> {
  timeout?: number;
}

function getBaseUrl(): string {
  if (typeof window !== 'undefined') {
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}

async function request<T>(
  endpoint: string,
  options: {
    method?: string;
    body?: unknown;
    timeout?: number;
  } & RequestOptions = {},
): Promise<T> {
  const { method = 'GET', body, timeout = DEFAULT_TIMEOUT_MS, headers, ...rest } = options;
  const url = `${getBaseUrl()}${endpoint}`;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
      ...rest,
    });

    if (!response.ok) {
      let errorBody: unknown;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text().catch(() => null);
      }
      throw new ApiError(response.status, response.statusText, errorBody, endpoint);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiTimeoutError(endpoint, timeout);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export const apiClient = {
  get: <T>(endpoint: string, opts?: RequestOptions) =>
    request<T>(endpoint, { method: 'GET', ...opts }),

  post: <T>(endpoint: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(endpoint, { method: 'POST', body, ...opts }),

  put: <T>(endpoint: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(endpoint, { method: 'PUT', body, ...opts }),

  patch: <T>(endpoint: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(endpoint, { method: 'PATCH', body, ...opts }),

  delete: <T>(endpoint: string, opts?: RequestOptions) =>
    request<T>(endpoint, { method: 'DELETE', ...opts }),
};

export type { RequestOptions };
