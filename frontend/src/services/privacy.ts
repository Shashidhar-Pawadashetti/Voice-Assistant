import { apiRequest } from './api';
import {
  DataExportResponse,
  DeletionRequestPayload,
  DeletionResponse,
} from '../types/privacy';

export const privacyService = {
  async exportData(): Promise<DataExportResponse> {
    return apiRequest<DataExportResponse>('/api/v1/privacy/export');
  },

  async deleteAccount(payload: DeletionRequestPayload): Promise<DeletionResponse> {
    return apiRequest<DeletionResponse>('/api/v1/privacy/delete', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
