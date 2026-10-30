/**
 * Base HTTP client for Krishi Mitra API.
 * Conforms to Directive M5, M6:
 * 1. Derives identity strictly from Bearer access token.
 * 2. Automatic refresh token rotation on token expiry.
 * 3. Never stores long-lived bearer tokens in permanent localStorage.
 * 4. Normalizes error envelopes.
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

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  isRetry: boolean = false
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const headers = new Headers(options.headers || {});

  // Inject Bearer token if available
  if (currentAccessToken && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${currentAccessToken}`);
  }

  // Set default JSON Content-Type if body is string
  if (options.body && typeof options.body === 'string' && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  try {
    const response = await fetch(url, { ...options, headers });

    // Handle 401 Unauthorized with token refresh if possible
    if (response.status === 401 && !isRetry && !path.includes('/auth/login') && !path.includes('/auth/refresh')) {
      const rt = getStoredRefreshToken();
      if (rt) {
        try {
          const refreshRes = await fetch(`${BASE_URL}/api/v1/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: rt }),
          });
          if (refreshRes.ok) {
            const data = await refreshRes.json();
            setTokens(data.access_token, data.refresh_token);
            // Retry original request with fresh access token
            return apiRequest<T>(path, options, true);
          } else {
            clearTokens();
          }
        } catch {
          clearTokens();
        }
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
        // Non-JSON error
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
