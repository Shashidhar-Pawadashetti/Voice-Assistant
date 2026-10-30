import test from 'node:test';
import assert from 'node:assert/strict';
import { kn } from '../src/i18n/kannada.ts';

test('Kannada localization contains all required top-level sections', () => {
  assert.ok(kn.app.title.includes('ಕೃಷಿ ಮಿತ್ರ'));
  assert.ok(kn.nav.dashboard);
  assert.ok(kn.nav.conversation);
  assert.ok(kn.nav.schemes);
  assert.ok(kn.nav.privacy);
  assert.ok(kn.voice.start);
  assert.ok(kn.voice.stopAndSend);
  assert.ok(kn.schemes.title);
  assert.ok(kn.schemes.disclaimer.includes('ಮಂಜೂರಾತಿ ಅಲ್ಲ') || kn.schemes.disclaimer.includes('ಅನುಮೋದನೆಯಲ್ಲ'));
  assert.ok(kn.schemes.demoNotice.includes('DEMO ONLY'));
  assert.ok(kn.privacy.exportTitle);
  assert.ok(kn.privacy.deleteTitle);
});

test('Kannada scheme statuses match backend RecommendationStatus enums', () => {
  const expectedStatuses = [
    'POTENTIALLY_MATCHED',
    'NOT_MATCHED',
    'INSUFFICIENT_INFORMATION',
    'VERIFICATION_REQUIRED',
    'RULES_NOT_VERIFIED',
  ];

  for (const status of expectedStatuses) {
    const label = (kn.schemes.status as Record<string, string>)[status];
    assert.ok(label, `Missing Kannada translation for status: ${status}`);
  }
});

test('Kannada dialogue states match backend DialogueState enums', () => {
  const expectedStates = [
    'GREETING',
    'COLLECTING_SLOTS',
    'CLARIFYING',
    'CONFIRMING',
    'EVALUATION_READY',
    'RESPONDING',
    'COMPLETED',
    'PAUSED',
  ];

  for (const state of expectedStates) {
    const label = (kn.dialogue.states as Record<string, string>)[state];
    assert.ok(label, `Missing Kannada translation for state: ${state}`);
  }
});
