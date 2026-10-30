import {
  apiRequest,
  clearTokens,
  getStoredRefreshToken,
  setTokens,
} from './api';
import {
  ChangePasswordRequest,
  FarmerResponse,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
} from '../types/auth';

export const authService = {
  async register(payload: RegisterRequest): Promise<{ farmer: FarmerResponse; tokens: TokenResponse }> {
    const data = await apiRequest<{ farmer: FarmerResponse; tokens: TokenResponse }>(
      '/api/v1/auth/register',
      {
        method: 'POST',
        body: JSON.stringify({
          ...payload,
          preferred_language: payload.preferred_language || 'kn',
          consent_given: payload.consent_given ?? true,
        }),
      }
    );
    setTokens(data.tokens.access_token, data.tokens.refresh_token);
    return data;
  },

  async login(payload: LoginRequest): Promise<TokenResponse> {
    const data = await apiRequest<TokenResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    setTokens(data.access_token, data.refresh_token);
    return data;
  },

  async getMe(): Promise<FarmerResponse> {
    return apiRequest<FarmerResponse>('/api/v1/auth/me');
  },

  async logout(): Promise<void> {
    const rt = getStoredRefreshToken();
    try {
      await apiRequest('/api/v1/auth/logout', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: rt }),
      });
    } catch {
      // Ignore network errors on logout
    } finally {
      clearTokens();
    }
  },

  async changePassword(payload: ChangePasswordRequest): Promise<void> {
    await apiRequest('/api/v1/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    // Password change revokes tokens on server; clear client tokens
    clearTokens();
  },

  async restoreSession(): Promise<FarmerResponse | null> {
    const rt = getStoredRefreshToken();
    if (!rt) return null;

    try {
      const tokens = await apiRequest<TokenResponse>('/api/v1/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: rt }),
      });
      setTokens(tokens.access_token, tokens.refresh_token);
      return await this.getMe();
    } catch {
      clearTokens();
      return null;
    }
  },
};
