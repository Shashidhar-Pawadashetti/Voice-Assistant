import { apiFetchBlob } from './api.ts';

const blobUrlCache = new Map<string, string>();

/**
 * Fetch owner-bound audio securely with Bearer authentication and convert to ephemeral Blob URL.
 * Automatically handles 401 token refresh via common API client.
 */
export async function fetchAuthenticatedAudioBlobUrl(audioPathOrUrl: string): Promise<string> {
  if (blobUrlCache.has(audioPathOrUrl)) {
    return blobUrlCache.get(audioPathOrUrl)!;
  }

  const blob = await apiFetchBlob(audioPathOrUrl);
  const objectUrl = URL.createObjectURL(blob);
  blobUrlCache.set(audioPathOrUrl, objectUrl);
  return objectUrl;
}

/**
 * Revoke single object URL.
 */
export function revokeAudioUrl(audioPathOrUrl: string): void {
  const url = blobUrlCache.get(audioPathOrUrl);
  if (url) {
    URL.revokeObjectURL(url);
    blobUrlCache.delete(audioPathOrUrl);
  }
}

/**
 * Cleanup created object URLs to prevent browser memory leaks.
 */
export function revokeAudioBlobUrls(): void {
  blobUrlCache.forEach((url) => {
    try {
      URL.revokeObjectURL(url);
    } catch {}
  });
  blobUrlCache.clear();
}
