export type SchemeClassification = 'REAL_GOVERNMENT' | 'SYNTHETIC_DEMO';
export type RecommendationStatus =
  | 'POTENTIALLY_MATCHED'
  | 'NOT_MATCHED'
  | 'INSUFFICIENT_INFORMATION'
  | 'VERIFICATION_REQUIRED'
  | 'RULES_NOT_VERIFIED';

export interface ConditionTrace {
  condition_id: string;
  field_name: string;
  operator: string;
  expected_value: any;
  actual_value?: any;
  result: 'TRUE' | 'FALSE' | 'UNKNOWN';
  reason?: string | null;
}

export interface EvidenceReference {
  authority: string;
  source_type: string;
  document_title: string;
  source_url?: string | null;
  publication_date?: string | null;
  official_verified: boolean;
}

export interface ExplanationTrace {
  scheme_id: string;
  display_name: string;
  display_name_kn: string;
  classification: SchemeClassification;
  recommendation_status: RecommendationStatus;
  official_verification_required: boolean;
  rule_version: string;
  evaluator_version?: string;
  matched_conditions: ConditionTrace[];
  failed_conditions: ConditionTrace[];
  unknown_conditions: ConditionTrace[];
  missing_slots: string[];
  unverified_conditions: ConditionTrace[];
  evidence_references: EvidenceReference[];
  kannada_explanation: string;
  english_summary: string;
  evaluated_at?: string;
}

export interface SchemeSummaryResponse {
  scheme_id: string;
  official_name: string;
  display_name: string;
  display_name_kn: string;
  classification: SchemeClassification;
  government_level: string;
  assistance_category: string;
  verification_status: string;
  demo_only: boolean;
  summary: string;
  summary_kn: string;
  application_portal?: string | null;
}

export interface SchemeDetailResponse extends SchemeSummaryResponse {
  description: string;
  description_kn: string;
  benefit_description: string;
  benefit_description_kn: string;
  application_procedure?: string | null;
  application_procedure_kn?: string | null;
  applicable_geography?: Record<string, any> | null;
  required_slots: string[];
  eligibility_conditions: any[];
  exclusions: any[];
  required_documents: string[];
  required_documents_kn: string[];
  evidence_references: EvidenceReference[];
  rule_version: string;
  dataset_version: string;
  official_verification_required: boolean;
  notes?: string | null;
}

export interface SchemeRecommendationResult {
  scheme_id: string;
  display_name: string;
  display_name_kn: string;
  classification: SchemeClassification;
  government_level: string;
  assistance_category: string;
  recommendation_status: RecommendationStatus;
  official_verification_required: boolean;
  demo_only: boolean;
  explanation_trace: ExplanationTrace;
  application_portal?: string | null;
}

export interface RecommendationEvaluationResponse {
  conversation_id: string;
  farmer_id: string;
  total_evaluated: number;
  recommendations: SchemeRecommendationResult[];
}
