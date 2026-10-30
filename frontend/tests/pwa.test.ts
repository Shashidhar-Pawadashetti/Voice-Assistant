import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

test('PWA manifest.json has valid standalone configuration and Kannada name', () => {
  const manifestPath = fs.existsSync('public/manifest.json')
    ? path.resolve('public/manifest.json')
    : path.resolve('frontend/public/manifest.json');
  assert.ok(fs.existsSync(manifestPath), 'manifest.json must exist');

  const content = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
  assert.ok(content.name.includes('ಕೃಷಿ ಮಿತ್ರ'));
  assert.equal(content.display, 'standalone');
  assert.equal(content.start_url, '/');
  assert.ok(content.icons.length >= 2);
});

test('Service Worker sw.js strictly enforces zero caching on authenticated API routes', () => {
  const swPath = fs.existsSync('public/sw.js')
    ? path.resolve('public/sw.js')
    : path.resolve('frontend/public/sw.js');
  assert.ok(fs.existsSync(swPath), 'sw.js must exist');

  const swCode = fs.readFileSync(swPath, 'utf-8');

  // Invariant 1: Must explicitly bypass caching for /api/
  assert.ok(
    swCode.includes("url.pathname.startsWith('/api/')"),
    'sw.js must explicitly check and bypass caching for /api/ routes'
  );

  // Invariant 2: Must explicitly bypass caching for /health/
  assert.ok(
    swCode.includes("url.pathname.startsWith('/health/')"),
    'sw.js must explicitly bypass caching for /health/ routes'
  );

  // Invariant 3: Must NOT contain raw audio upload queues in sw.js
  assert.ok(
    !swCode.includes('backgroundSync') || !swCode.includes('uploadAudio'),
    'sw.js must not silently queue raw audio for background upload'
  );
});
