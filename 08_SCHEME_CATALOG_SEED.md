# 08 — Reference Scheme Catalog Seed

## 1. Source dataset supplied for the challenge

The prototype reference table supplied by the project owner lists:

| Scheme | Type | Use in prototype |
|---|---|---|
| PM-KISAN | Real | Income assistance for eligible landholding farmer families; verify official exclusions and enrolment requirements. |
| PMFBY | Real | Crop insurance subject to crop, notified area, season and applicable government rules. |
| Demo Micro-Irrigation Support | Fictional | Synthetic test case for drip irrigation support; no real entitlement implied. |
| Demo Agricultural Equipment Assistance | Fictional | Synthetic test case for equipment subsidy decision rules. |
| Demo Soil Improvement Support | Fictional | Synthetic test case for additional rule-based recommendation paths. |

## 2. Catalog seed policy

The five records must be present in the local development catalog. However, the real schemes must initially have `verification_status: INCOMPLETE` unless the developer has encoded and independently tested the applicable official rule set. This intentionally prevents invented rule behavior.

Fictional records must carry `classification: SYNTHETIC_DEMO` and be visually/API labelled `DEMO_ONLY` at every layer.

## 3. Seed records

### PM-KISAN

```json
{
  "scheme_id": "PM_KISAN",
  "display_name": "PM-KISAN",
  "classification": "REAL_GOVERNMENT",
  "government_level": "CENTRAL",
  "assistance_category": "INCOME_SUPPORT",
  "official_source_urls": ["https://pmkisan.gov.in/"],
  "verification_status": "INCOMPLETE",
  "rule_version": "0.0.0",
  "note": "Do not infer entitlement from land ownership alone. Official exclusions and current enrolment/eKYC requirements must be encoded from current primary guidance before a real recommendation is enabled."
}
```

### PMFBY

```json
{
  "scheme_id": "PMFBY",
  "display_name": "Pradhan Mantri Fasal Bima Yojana",
  "classification": "REAL_GOVERNMENT",
  "government_level": "CENTRAL",
  "assistance_category": "CROP_INSURANCE",
  "official_source_urls": ["https://pmfby.gov.in/"],
  "verification_status": "INCOMPLETE",
  "rule_version": "0.0.0",
  "note": "Requires current season, crop, notified area and applicable state/district notification. Never recommend based only on crop name."
}
```

### Demo Micro-Irrigation Support

```json
{
  "scheme_id": "DEMO_MICRO_IRRIGATION",
  "display_name": "Demo Micro-Irrigation Support",
  "classification": "SYNTHETIC_DEMO",
  "government_level": "NONE",
  "assistance_category": "MICRO_IRRIGATION",
  "verification_status": "VERIFIED_FOR_DEMO_ONLY",
  "rule_version": "1.0.0",
  "demo_only": true,
  "note": "Synthetic rule path for testing a drip-irrigation request. It is not a government scheme and implies no entitlement."
}
```

### Demo Agricultural Equipment Assistance

```json
{
  "scheme_id": "DEMO_EQUIPMENT_ASSISTANCE",
  "display_name": "Demo Agricultural Equipment Assistance",
  "classification": "SYNTHETIC_DEMO",
  "government_level": "NONE",
  "assistance_category": "AGRICULTURAL_EQUIPMENT",
  "verification_status": "VERIFIED_FOR_DEMO_ONLY",
  "rule_version": "1.0.0",
  "demo_only": true,
  "note": "Synthetic decision-rule test path. Do not represent as a real subsidy."
}
```

### Demo Soil Improvement Support

```json
{
  "scheme_id": "DEMO_SOIL_IMPROVEMENT",
  "display_name": "Demo Soil Improvement Support",
  "classification": "SYNTHETIC_DEMO",
  "government_level": "NONE",
  "assistance_category": "SOIL_IMPROVEMENT",
  "verification_status": "VERIFIED_FOR_DEMO_ONLY",
  "rule_version": "1.0.0",
  "demo_only": true,
  "note": "Synthetic test path for additional rule-based recommendation flows."
}
```

## 4. Important implementation limitation

The project brief does not supply complete synthetic decision conditions, thresholds, benefit amounts, document lists or application steps for the three demo schemes. Therefore:

- The developer may create clearly artificial test fixtures only when labelled as test data and kept out of real-world recommendation wording.
- Do not invent an amount, subsidy percentage, land threshold, deadline or document checklist and display it as factual.
- Ask the project owner to approve any synthetic conditions intended for a live demonstration.

## 5. Official sources to consult

- PM-KISAN: https://pmkisan.gov.in/
- PMFBY: https://pmfby.gov.in/
- PMFBY guidelines/notifications: use official portal documents applicable to the requested season and state.

The developer must record exact document titles, publication dates, effective periods and cited sections in the catalog. A portal homepage alone is not enough evidence for a specific rule.

## 6. Safe initial behavior

Until real criteria are verified:

- the API may display scheme descriptions with a “rules not verified” label;
- the dialogue may collect the relevant facts;
- the evaluator must return `RULES_NOT_VERIFIED` for real schemes;
- demo schemes can be exercised through synthetic fixtures with a persistent `DEMO_ONLY` marker.
