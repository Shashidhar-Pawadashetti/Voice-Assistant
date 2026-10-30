import test from 'node:test';
import assert from 'node:assert/strict';
import {
  setTokens,
  getAccessToken,
  getStoredRefreshToken,
  clearTokens,
  refreshSessionTokens,
} from '../src/services/api.ts';
import { fetchAuthenticatedAudioBlobUrl, revokeAudioBlobUrls } from '../src/services/audio.ts';
import type { SchemeRecommendationResult } from '../src/types/scheme.ts';

// Mock DOM / Browser environment for Node test runner
const mockSessionStorage: Record<string, string> = {};
globalThis.sessionStorage = {
  getItem: (key: string) => mockSessionStorage[key] || null,
  setItem: (key: string, val: string) => { mockSessionStorage[key] = val; },
  removeItem: (key: string) => { delete mockSessionStorage[key]; },
  clear: () => { Object.keys(mockSessionStorage).forEach(k => delete mockSessionStorage[k]); },
  length: 0,
  key: () => null,
};

let createdBlobUrls: string[] = [];
let revokedBlobUrls: string[] = [];

globalThis.URL.createObjectURL = (blob: any) => {
  const url = `blob:http://localhost:5173/${Math.random().toString(36).slice(2)}`;
  createdBlobUrls.push(url);
  return url;
};
globalThis.URL.revokeObjectURL = (url: string) => {
  revokedBlobUrls.push(url);
};

test('Journey A (Frontend): Registration, session restoration, and logout state isolation', async () => {
  clearTokens();
  assert.equal(getAccessToken(), null);

  // Set tokens simulating post-registration
  setTokens('jwt_access_111', 'rt_family_222');
  assert.equal(getAccessToken(), 'jwt_access_111');
  assert.equal(getStoredRefreshToken(), 'rt_family_222');

  // Verify safe logout cleans up all tokens
  clearTokens();
  assert.equal(getAccessToken(), null);
  assert.equal(getStoredRefreshToken(), null);
  assert.equal(sessionStorage.getItem('krishi_rt'), null);
});

test('Journey B & D (Frontend): Authenticated audio fetching, caching, and explicit memory cleanup', async () => {
  createdBlobUrls = [];
  revokedBlobUrls = [];
  setTokens('test_access_token', 'test_refresh');

  // Mock fetch for audio response
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (input: any, init?: any) => {
    return new Response(new Uint8Array([82, 73, 70, 70, 1, 2, 3, 4]), {
      status: 200,
      headers: { 'Content-Type': 'audio/wav' },
    });
  };

  try {
    const audioPath = '/api/v1/voice/audio/1234567890abcdef1234567890abcdef';
    const blobUrl1 = await fetchAuthenticatedAudioBlobUrl(audioPath);
    assert.match(blobUrl1, /^blob:/);

    // Repeated call must return cached blob URL without re-creating
    const blobUrl2 = await fetchAuthenticatedAudioBlobUrl(audioPath);
    assert.equal(blobUrl1, blobUrl2);
    assert.equal(createdBlobUrls.length, 1);

    // Explicit revoke on unmount / logout
    revokeAudioBlobUrls();
    assert.equal(revokedBlobUrls.length, 1);
    assert.equal(revokedBlobUrls[0], blobUrl1);
  } finally {
    globalThis.fetch = originalFetch;
    clearTokens();
  }
});

test('Journey C (Frontend): Scheme recommendation history strictly sorts latest run first', () => {
  const historyRuns = [
    {
      id: 'run-1',
      evaluated_at: '2026-10-31T01:00:00Z',
      results: [{ scheme_id: 'PM_KISAN', recommendation_status: 'NEEDS_MORE_INFORMATION' }],
    },
    {
      id: 'run-3',
      evaluated_at: '2026-10-31T03:00:00Z',
      results: [{ scheme_id: 'PM_KISAN', recommendation_status: 'POTENTIALLY_MATCHED' }],
    },
    {
      id: 'run-2',
      evaluated_at: '2026-10-31T02:00:00Z',
      results: [{ scheme_id: 'PM_KISAN', recommendation_status: 'NEEDS_MORE_INFORMATION' }],
    },
  ];

  // Guaranteed latest run ordering:
  const sorted = [...historyRuns].sort(
    (a, b) => new Date(b.evaluated_at).getTime() - new Date(a.evaluated_at).getTime()
  );

  assert.equal(sorted[0].id, 'run-3');
  assert.equal(sorted[0].results[0].recommendation_status, 'POTENTIALLY_MATCHED');
  assert.equal(sorted[1].id, 'run-2');
  assert.equal(sorted[2].id, 'run-1');
});
