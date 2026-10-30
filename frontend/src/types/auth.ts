export interface RegisterRequest {
  phone_number: string;
  password: string;
  preferred_language?: string;
  consent_given?: boolean;
}

export interface LoginRequest {
  phone_number: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface FarmerResponse {
  id: string;
  phone_number_masked: string;
  preferred_language: string;
  account_status: 'ACTIVE' | 'LOCKED' | 'DELETION_PENDING' | 'DELETED';
  created_at: string;
  last_login_at?: string | null;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}
