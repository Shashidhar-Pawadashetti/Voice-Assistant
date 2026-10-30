import { getAccessToken } from './api';

const BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) || '';
const blobUrlCache = new Map<string, string>();

/**
 * Fetch owner-bound audio securely with Bearer authentication and convert to ephemeral Blob URL.
 */
export async function fetchAuthenticatedAudioBlobUrl(audioPathOrUrl: string): Promise<string> {
  if (blobUrlCache.has(audioPathOrUrl)) {
    return blobUrlCache.get(audioPathOrUrl)!;
  }

  const url = audioPathOrUrl.startsWith('http') ? audioPathOrUrl : `${BASE_URL}${audioPathOrUrl}`;
  const token = getAccessToken();
  const headers = new Headers();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const res = await fetch(url, { headers });
  if (!res.ok) {
    throw new Error(`Failed to load audio response: ${res.status}`);
  }

  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  blobUrlCache.set(audioPathOrUrl, objectUrl);
  return objectUrl;
}

/**
 * Cleanup created object URLs to prevent browser memory leaks.
 */
export function revokeAudioBlobUrls() {
  blobUrlCache.forEach((url) => URL.revokeObjectURL(url));
  blobUrlCache.clear();
}
