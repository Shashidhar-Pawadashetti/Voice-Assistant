# M4 — Government Scheme Intelligence & Explainable Recommendation Engine

## 1. Overview and Core Philosophy

Milestone M4 delivers a deterministic, auditable, and evidence-backed government scheme recommendation engine for the Krishi Mitra AI backend.

### Non-Negotiable Invariants Upheld
1. **The LLM Never Decides Eligibility**: Scheme conditions are evaluated entirely in pure, deterministic Python code without using an LLM, `eval`, `exec`, or raw SQL expressions.
2. **Strict Three-Valued Logic**: Every condition evaluates to `TRUE`, `FALSE`, or `UNKNOWN`. Missing or unverified information produces `UNKNOWN`, preventing speculative recommendations.
3. **Real vs Synthetic Demonstration Isolation**: Real government schemes (`PM_KISAN`, `PMFBY`) are strictly distinguished from synthetic test fixtures (`DEMO_MICRO_IRRIGATION`, `DEMO_EQUIPMENT_ASSISTANCE`, `DEMO_SOIL_IMPROVEMENT`). Synthetic schemes carry persistent `DEMO_ONLY` markers at all API and dialogue layers.
4. **No Entitlement Approval Claims**: The assistant never states "you are approved" or "you will receive ₹X". Output outcomes are cautious: `POTENTIALLY_MATCHED`, `NOT_MATCHED`, `INSUFFICIENT_INFORMATION`, `VERIFICATION_REQUIRED`, or `RULES_NOT_VERIFIED`.
5. **No Invented Rules or Criteria**: Official guidelines were consulted for real schemes. If current seasonal gazette notifications are unavailable, schemes are preserved as `INCOMPLETE`, blocking evaluation via `RULES_NOT_VERIFIED`.

---

## 2. Architecture & Subsystem Structure

```
                                      +--------------------------+
                                      |   M3 Conversation Turn   |
                                      +-------------+------------+
                                                    |
                                                    v
+------------------------+             +--------------------------+
|  Agricultural Profile  | ----------> |  RecommendationService   |
|   (M2 Verified Facts)  |             +-------------+------------+
+------------------------+                           |
                                                     |
                     +-------------------------------+-------------------------------+
                     |                                                               |
                     v                                                               v
      +------------------------------+                                +------------------------------+
      |    SchemeCatalogRepository   |                                |     EligibilityEvaluator     |
      |   (PostgreSQL & Catalog)     |                                |   (3-Valued Deterministic)   |
      +--------------+---------------+                                +--------------+---------------+
                     |                                                               |
                     +-------------------------------+-------------------------------+
                                                     |
                                                     v
                                      +--------------------------+
                                      |     ExplanationTrace     |
                                      |  (Machine-Readable Trace)|
                                      +-------------+------------+
                                                    |
                        +---------------------------+---------------------------+
                        |                                                       |
                        v                                                       v
         +------------------------------+                        +------------------------------+
         |     RecommendationRun        |                        |  format_grounded_kannada_... |
         |   (Immutable PostgreSQL DB)  |                        |    (Native Spoken Kannada)   |
         +------------------------------+                        +------------------------------+
```

---

## 3. Controlled Declarative Rule Format

Rule definitions are pure declarative data validated via Pydantic (`RuleCondition`, `RuleGroup`, `SchemeDefinition`).

### Permitted Operators
| Operator | Type | Semantics |
|---|---|---|
| `EQ` | Binary | Equality check (case-insensitive for strings) |
| `NEQ` | Binary | Inequality check |
| `IN` | Collection | Membership check in expected sequence or set |
| `NOT_IN` | Collection | Non-membership check |
| `GT`, `GTE` | Numeric | Decimal-aware numerical greater-than / greater-than-equal |
| `LT`, `LTE` | Numeric | Decimal-aware numerical less-than / less-than-equal |
| `EXISTS` | Presence | Value is present, non-null, and non-empty |
| `AND` | Compound Group | Short-circuit conjunction truth table |
| `OR` | Compound Group | Short-circuit disjunction truth table |
| `NOT` | Compound Group | Three-valued logical negation |

---

## 4. Three-Valued Logic Truth Tables

Conditions evaluate to `TRUE`, `FALSE`, or `UNKNOWN`.

### Boolean Connectives
| Left Operand | Operator | Right Operand | Result |
|---|---|---|---|
| `TRUE` | `AND` | `TRUE` | `TRUE` |
| `TRUE` | `AND` | `UNKNOWN` | `UNKNOWN` |
| `FALSE` | `AND` | `UNKNOWN` | `FALSE` |
| `FALSE` | `AND` | `TRUE` | `FALSE` |
| `UNKNOWN` | `AND` | `UNKNOWN` | `UNKNOWN` |
| `TRUE` | `OR` | `UNKNOWN` | `TRUE` |
| `FALSE` | `OR` | `UNKNOWN` | `UNKNOWN` |
| `FALSE` | `OR` | `FALSE` | `FALSE` |
| `TRUE` | `OR` | `FALSE` | `TRUE` |
| `UNKNOWN` | `OR` | `UNKNOWN` | `UNKNOWN` |

### Logical Negation (`NOT`)
- `NOT TRUE` $\rightarrow$ `FALSE`
- `NOT FALSE` $\rightarrow$ `TRUE`
- `NOT UNKNOWN` $\rightarrow$ `UNKNOWN`

---

## 5. Official Government Scheme Verification Matrix

| Scheme ID | Classification | Authority & Source | Official Guidelines Citation | Verification Status | Evaluator Outcome |
|---|---|---|---|---|---|
| `PM_KISAN` | `REAL_GOVERNMENT` | Department of Agriculture & FW, Ministry of Agriculture & FW, GoI (https://pmkisan.gov.in/) | Operational Guidelines PM-KISAN Clause 2(b) (Beneficiary Definition) & Clause 3 (Institutional and Tax Exclusions) | `VERIFIED` | `VERIFICATION_REQUIRED` (for self-stated facts) / `POTENTIALLY_MATCHED` (when verified) |
| `PMFBY` | `REAL_GOVERNMENT` | Ministry of Agriculture & FW, GoI (https://pmfby.gov.in/) | Revised Operational Guidelines PMFBY Section II & III (Requires current seasonal gazette notification) | `INCOMPLETE` | `RULES_NOT_VERIFIED` (prevents invented crop insurance claims) |
| `DEMO_MICRO_IRRIGATION` | `SYNTHETIC_DEMO` | Krishi Mitra Prototype Specification 08 | Synthetic decision tree for drip/sprinkler test fixtures | `VERIFIED_FOR_DEMO_ONLY` | `POTENTIALLY_MATCHED` (`DEMO_ONLY` marker) |
| `DEMO_EQUIPMENT_ASSISTANCE` | `SYNTHETIC_DEMO` | Krishi Mitra Prototype Specification 08 | Synthetic decision tree for equipment subsidy test fixtures | `VERIFIED_FOR_DEMO_ONLY` | `POTENTIALLY_MATCHED` (`DEMO_ONLY` marker) |
| `DEMO_SOIL_IMPROVEMENT` | `SYNTHETIC_DEMO` | Krishi Mitra Prototype Specification 08 | Synthetic decision tree for soil amendment test fixtures | `VERIFIED_FOR_DEMO_ONLY` | `POTENTIALLY_MATCHED` (`DEMO_ONLY` marker) |

---

## 6. Database Schema & Migration `0003_scheme_catalogue_m4`

The PostgreSQL relational catalog was extended to include localized metadata and version tracking:

### Extended `schemes` Table
- `display_name_kn`: Native Kannada title (`VARCHAR(255)`)
- `description`, `description_kn`: Localized descriptions (`TEXT`)
- `benefit_description`, `benefit_description_kn`: Localized entitlements breakdown (`TEXT`)
- `application_portal`: Official portal URL (`VARCHAR(500)`)
- `applicable_geography`: Geographic boundaries JSON (`JSONB` / Portable JSON)
- `dataset_version`: Release version tag (Default `"2026.1"`)

### Immutable `recommendation_runs` Table
- `id`: `UUID` Primary Key
- `farmer_id`: Foreign Key (`farmers.id`)
- `conversation_id`: Foreign Key (`conversations.id`)
- `profile_snapshot`: JSON snapshot of farmer's agricultural facts at evaluation time
- `scheme_rule_version_id`: Foreign Key (`scheme_rule_versions.id`)
- `evaluator_version`: Engine version (e.g. `"v1.0.0"`)
- `outcome`: Recommendation outcome status string
- `explanation_trace`: Complete machine-readable condition trace and evidence citations
- `evaluated_at`: UTC Timestamp

---

## 7. REST API Endpoints

1. `GET /api/v1/schemes`: List active government and demonstration schemes. Filterable by `classification` and `category`.
2. `GET /api/v1/schemes/{scheme_id}`: Full scheme definition, conditions, exclusions, documents, and evidence citations.
3. `POST /api/v1/conversations/{conversation_id}/recommendations`: Evaluates applicable schemes for the conversation profile, records an immutable `recommendation_runs` entry, and returns structured traces. Enforces `x-farmer-id` BOLA ownership.
4. `GET /api/v1/conversations/{conversation_id}/recommendations`: Returns chronological audit traces for all previous recommendation runs of that conversation.

---

## 8. M3 Dialogue Integration

When a farmer conversation completes missing slots and arrives at `DialogueState.EVALUATION_READY`:
1. `RecommendationService.evaluate_for_farmer` evaluates candidate schemes deterministically.
2. An immutable evaluation trace is saved in PostgreSQL.
3. Grounded Kannada explanation text is returned in `TurnResponse.assistant_text`.
4. Indic-TTS synthesizes the spoken response, advising official verification at the relevant government portal.
