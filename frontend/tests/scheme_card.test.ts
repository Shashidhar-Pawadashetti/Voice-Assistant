import test from 'node:test';
import assert from 'node:assert/strict';
import type { SchemeRecommendationResult } from '../src/types/scheme.ts';

test('Scheme recommendation model handles DEMO_ONLY and status variants correctly', () => {
  const syntheticRecommendation: SchemeRecommendationResult = {
    scheme_id: 'DEMO_MICRO_IRRIGATION',
    display_name: 'Demonstration Drip Scheme',
    display_name_kn: 'ಮಾದರಿ ಹನಿ ನೀರಾವರಿ ಯೋಜನೆ',
    classification: 'SYNTHETIC_DEMO',
    government_level: 'STATE',
    assistance_category: 'IRRIGATION',
    recommendation_status: 'POTENTIALLY_MATCHED',
    official_verification_required: true,
    demo_only: true,
    application_portal: null,
    explanation_trace: {
      scheme_id: 'DEMO_MICRO_IRRIGATION',
      display_name: 'Demonstration Drip Scheme',
      display_name_kn: 'ಮಾದರಿ ಹನಿ ನೀರಾವರಿ ಯೋಜನೆ',
      classification: 'SYNTHETIC_DEMO',
      recommendation_status: 'POTENTIALLY_MATCHED',
      official_verification_required: true,
      rule_version: '1.0.0',
      matched_conditions: [],
      failed_conditions: [],
      unknown_conditions: [],
      missing_slots: [],
      unverified_conditions: [],
      evidence_references: [],
      kannada_explanation: 'ಡೆಮೊ ವಿವರಣೆ',
      english_summary: 'Demo explanation',
    },
  };

  assert.equal(syntheticRecommendation.demo_only, true);
  assert.equal(syntheticRecommendation.classification, 'SYNTHETIC_DEMO');
  assert.equal(syntheticRecommendation.recommendation_status, 'POTENTIALLY_MATCHED');
  assert.ok(syntheticRecommendation.official_verification_required);
});
