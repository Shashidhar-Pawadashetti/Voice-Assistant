/**
 * Base HTTP client for Krishi Mitra API.
 * Conforms to Directive M5, M6, and M7:
 * 1. Derives identity strictly from Bearer access token.
 * 2. Concurrency-safe automatic refresh token rotation using shared promise mutex.
 * 3. Unified client for text (JSON), voice (FormData), and audio streams (Blob).
 * 4. Never stores long-lived bearer tokens in permanent localStorage.
 * 5. Robust error parsing and offline resilience.
 */

export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: Record<string, any>;
  retryable?: boolean;
}

export class ApiError extends Error {
  code: string;
  statusCode: number;
  details?: Record<string, any>;

  constructor(message: string, code: string, statusCode: number, details?: Record<string, any>) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

// In-memory token storage
let currentAccessToken: string | null = null;
let currentRefreshToken: string | null = null;

export const setTokens = (accessToken: string | null, refreshToken: string | null) => {
  currentAccessToken = accessToken;
  currentRefreshToken = refreshToken;
  if (refreshToken) {
    sessionStorage.setItem('krishi_rt', refreshToken);
  } else {
    sessionStorage.removeItem('krishi_rt');
  }
};

export const getAccessToken = (): string | null => currentAccessToken;
export const getStoredRefreshToken = (): string | null => {
  return currentRefreshToken || sessionStorage.getItem('krishi_rt');
};

export const clearTokens = () => {
  currentAccessToken = null;
  currentRefreshToken = null;
  sessionStorage.removeItem('krishi_rt');
};

const BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) || '';

// Concurrency-safe refresh mutex (M7.1, M7.2)
let activeRefreshPromise: Promise<boolean> | null = null;

export async function refreshSessionTokens(): Promise<boolean> {
  if (activeRefreshPromise) {
    return activeRefreshPromise;
  }

  activeRefreshPromise = (async () => {
    const rt = getStoredRefreshToken();
    if (!rt) {
      clearTokens();
      return false;
    }
    try {
      const res = await fetch(`${BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: rt }),
      });
      if (res.ok) {
        const data = await res.json();
        setTokens(data.access_token, data.refresh_token);
        return true;
      } else {
        clearTokens();
        return false;
      }
    } catch {
      // In offline / network drop, keep refresh token for recovery later
      return false;
    } finally {
      activeRefreshPromise = null;
    }
  })();

  return activeRefreshPromise;
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  isRetry: boolean = false
): Promise<T> {
  const url = path.startsWith('http') ? path : `${BASE_URL}${path}`;
  const headers = new Headers(options.headers || {});

  // Inject Bearer token if available
  if (currentAccessToken && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${currentAccessToken}`);
  }

  // Set default JSON Content-Type only if body is a string (leaves FormData untouched)
  if (options.body && typeof options.body === 'string' && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  try {
    const response = await fetch(url, { ...options, headers });

    // Handle 401 Unauthorized with concurrency-safe token refresh
    if (response.status === 401 && !isRetry && !path.includes('/auth/login') && !path.includes('/auth/refresh')) {
      const refreshed = await refreshSessionTokens();
      if (refreshed) {
        const retryHeaders = new Headers(options.headers || {});
        if (currentAccessToken) {
          retryHeaders.set('Authorization', `Bearer ${currentAccessToken}`);
        }
        return apiRequest<T>(path, { ...options, headers: retryHeaders }, true);
      }
    }

    if (!response.ok) {
      let errorMsg = `Request failed with status ${response.status}`;
      let errorCode = 'API_ERROR';
      let details: Record<string, any> | undefined;

      try {
        const json = await response.json();
        if (json.error) {
          errorMsg = json.error.message || errorMsg;
          errorCode = json.error.code || errorCode;
          details = json.error.details;
        } else if (json.detail) {
          errorMsg = typeof json.detail === 'string' ? json.detail : JSON.stringify(json.detail);
        }
      } catch {
        // Non-JSON error body
      }

      throw new ApiError(errorMsg, errorCode, response.status, details);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return await response.json();
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    // Network or offline error
    throw new ApiError(
      'ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕವಿಲ್ಲ ಅಥವಾ ಸರ್ವರ್ ಲಭ್ಯವಿಲ್ಲ (Network connection error)',
      'NETWORK_OFFLINE',
      0
    );
  }
}

/**
 * Common authenticated blob fetcher with 401 refresh coordination.
 */
export async function apiFetchBlob(
  path: string,
  options: RequestInit = {},
  isRetry: boolean = false
): Promise<Blob> {
  const url = path.startsWith('http') ? path : `${BASE_URL}${path}`;
  const headers = new Headers(options.headers || {});

  if (currentAccessToken && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${currentAccessToken}`);
  }

  try {
    const response = await fetch(url, { ...options, headers });

    if (response.status === 401 && !isRetry && !path.includes('/auth/login') && !path.includes('/auth/refresh')) {
      const refreshed = await refreshSessionTokens();
      if (refreshed) {
        const retryHeaders = new Headers(options.headers || {});
        if (currentAccessToken) {
          retryHeaders.set('Authorization', `Bearer ${currentAccessToken}`);
        }
        return apiFetchBlob(path, { ...options, headers: retryHeaders }, true);
      }
    }

    if (!response.ok) {
      throw new ApiError(`Failed to fetch media stream (${response.status})`, 'MEDIA_FETCH_FAILED', response.status);
    }

    return await response.blob();
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      'ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕವಿಲ್ಲ (Network connection error)',
      'NETWORK_OFFLINE',
      0
    );
  }
}
