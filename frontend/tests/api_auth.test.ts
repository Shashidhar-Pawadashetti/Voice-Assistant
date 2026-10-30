import test from 'node:test';
import assert from 'node:assert/strict';
import {
  setTokens,
  getAccessToken,
  getStoredRefreshToken,
  clearTokens,
} from '../src/services/api.ts';

// Mock sessionStorage in Node environment
const mockSessionStorage: Record<string, string> = {};
globalThis.sessionStorage = {
  getItem: (key: string) => mockSessionStorage[key] || null,
  setItem: (key: string, val: string) => { mockSessionStorage[key] = val; },
  removeItem: (key: string) => { delete mockSessionStorage[key]; },
  clear: () => { Object.keys(mockSessionStorage).forEach(k => delete mockSessionStorage[k]); },
  length: 0,
  key: () => null,
};

test('Tokens are managed in memory and sessionStorage safely', () => {
  clearTokens();
  assert.equal(getAccessToken(), null);
  assert.equal(getStoredRefreshToken(), null);

  // Set tokens
  setTokens('access_token_123', 'refresh_token_abc');
  assert.equal(getAccessToken(), 'access_token_123');
  assert.equal(getStoredRefreshToken(), 'refresh_token_abc');
  assert.equal(sessionStorage.getItem('krishi_rt'), 'refresh_token_abc');

  // Invariant: Clear tokens on logout
  clearTokens();
  assert.equal(getAccessToken(), null);
  assert.equal(getStoredRefreshToken(), null);
  assert.equal(sessionStorage.getItem('krishi_rt'), null);
});
