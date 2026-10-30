export interface DataExportResponse {
  export_generated_at: string;
  farmer_id: string;
  preferred_language: string;
  account_status: string;
  created_at: string;
  last_login_at?: string | null;
  profile_data: Record<string, any>;
  consent_history: Array<Record<string, any>>;
  conversations: Array<Record<string, any>>;
  recommendation_runs: Array<Record<string, any>>;
}

export interface DeletionRequestPayload {
  password: string;
  reason?: string | null;
}

export interface DeletionResponse {
  status: string;
  message: string;
  requested_at: string;
  completed_at: string;
  deletion_request_id: string;
  records_erased: Record<string, number>;
}
