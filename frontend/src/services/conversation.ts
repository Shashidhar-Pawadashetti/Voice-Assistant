import { apiRequest, getAccessToken } from './api';
import {
  ConversationResponse,
  ConversationTurnDTO,
  TurnResponse,
} from '../types/conversation';

const BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) || '';

export const conversationService = {
  async getActive(): Promise<ConversationResponse | null> {
    try {
      return await apiRequest<ConversationResponse>('/api/v1/conversations/active');
    } catch (err: any) {
      if (err.statusCode === 404) return null;
      throw err;
    }
  },

  async create(language: string = 'kn'): Promise<ConversationResponse> {
    return apiRequest<ConversationResponse>('/api/v1/conversations', {
      method: 'POST',
      body: JSON.stringify({ language }),
    });
  },

  async getById(conversationId: string): Promise<ConversationResponse> {
    return apiRequest<ConversationResponse>(`/api/v1/conversations/${conversationId}`);
  },

  async list(status?: string, limit: number = 20, offset: number = 0): Promise<{ conversations: ConversationResponse[]; total: number }> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (status) params.append('status', status);
    return apiRequest<{ conversations: ConversationResponse[]; total: number }>(`/api/v1/conversations?${params.toString()}`);
  },

  async submitTextTurn(
    conversationId: string,
    text: string,
    expectedVersion?: number | null
  ): Promise<TurnResponse> {
    const clientTurnId = crypto.randomUUID();
    return apiRequest<TurnResponse>(`/api/v1/conversations/${conversationId}/turns/text`, {
      method: 'POST',
      body: JSON.stringify({
        text,
        language: 'kn',
        client_turn_id: clientTurnId,
        expected_version: expectedVersion,
      }),
    });
  },

  async submitVoiceTurn(
    conversationId: string,
    audioBlob: Blob
  ): Promise<TurnResponse> {
    const clientTurnId = crypto.randomUUID();
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');
    formData.append('language', 'kn');
    formData.append('client_turn_id', clientTurnId);

    const token = getAccessToken();
    const headers = new Headers();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    const res = await fetch(`${BASE_URL}/api/v1/conversations/${conversationId}/turns/voice`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!res.ok) {
      let msg = 'ಧ್ವನಿ ಪ್ರಕ್ರಿಯೆ ವಿಫಲವಾಗಿದೆ (Voice turn submission failed)';
      try {
        const j = await res.json();
        if (j.error?.message) msg = j.error.message;
      } catch {}
      throw new Error(msg);
    }

    return await res.json();
  },

  async getTurns(conversationId: string): Promise<ConversationTurnDTO[]> {
    const data = await apiRequest<{ turns: ConversationTurnDTO[] }>(
      `/api/v1/conversations/${conversationId}/turns`
    );
    return data.turns || [];
  },

  async resume(conversationId: string): Promise<ConversationResponse> {
    return apiRequest<ConversationResponse>(`/api/v1/conversations/${conversationId}/resume`, {
      method: 'POST',
    });
  },

  async complete(conversationId: string): Promise<ConversationResponse> {
    return apiRequest<ConversationResponse>(`/api/v1/conversations/${conversationId}/complete`, {
      method: 'POST',
    });
  },
};
