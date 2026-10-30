import { apiRequest } from './api';
import {
  RecommendationEvaluationResponse,
  SchemeDetailResponse,
  SchemeSummaryResponse,
} from '../types/scheme';

export const schemeService = {
  async list(classification?: string, category?: string): Promise<SchemeSummaryResponse[]> {
    const params = new URLSearchParams();
    if (classification) params.append('classification', classification);
    if (category) params.append('category', category);
    const query = params.toString() ? `?${params.toString()}` : '';
    return apiRequest<SchemeSummaryResponse[]>(`/api/v1/schemes${query}`);
  },

  async getDetail(schemeId: string): Promise<SchemeDetailResponse> {
    return apiRequest<SchemeDetailResponse>(`/api/v1/schemes/${schemeId}`);
  },

  async evaluate(conversationId: string): Promise<RecommendationEvaluationResponse> {
    return apiRequest<RecommendationEvaluationResponse>(
      `/api/v1/conversations/${conversationId}/recommendations`,
      { method: 'POST' }
    );
  },

  async getHistory(conversationId: string): Promise<any[]> {
    return apiRequest<any[]>(`/api/v1/conversations/${conversationId}/recommendations`);
  },
};
