# Krishi Mitra — Milestone M8: Automated Synthetic Cohort Validation Report

**Execution Timestamp:** 2026-10-31 03:45:33 UTC  
**Software Version:** 1.0.0  
**Commit SHA:** `2213d11eceecaaa7ec4ed14e24766de8833c36a0`  
**Evidence Classification:** `AUTOMATED_TEST` (Executed via in-process ASGI test harness)  
**Harness File:** `scripts/run_pilot_field_trial.py`  
**Metrics Source:** `docs/m8_automated_validation_metrics.json` (SHA-256: `64a732ce23dcbb26d55d0467971555516593f585c79a1aea746c29586ff08d40`)  
**Overall Verdict:** **PASSED (100% of required assertions)**  

> [!IMPORTANT]
> **MANDATORY EVIDENCE INTEGRITY NOTICE:**
> This report records results from an **automated synthetic simulation harness**. Under no circumstances should this automated result be represented as a real-world farmer field observation or real rural network performance benchmark.
> - **Participants:** 20 predefined synthetic test fixtures (`SF01` to `SF20`). Zero real farmers participated.
> - **Speech Pipeline:** MockSpeechRecognizer (ASR) and MockSpeechSynthesizer (TTS).
> - **NLU Extraction:** Deterministic rule parser simulating local model extraction.
> - **Latency Profile:** In-process ASGI memory-loop execution (p50 = 97.7 ms). Does not reflect rural 3G/4G network latency.

---

## 1. Executive Summary & Verification Metrics

| Metric | Value | Classification | Meaning / Context |
| :--- | :--- | :--- | :--- |
| **Synthetic Fixtures Evaluated** | 20 fixtures | `[AUTOMATED_TEST: FIXTURES]` | 20 agro-climatic persona fixtures across 4 Karnataka zones |
| **Assertions Required** | 294 assertions | `[AUTOMATED_TEST]` | Required test assertions across all scenarios |
| **Assertions Exercised** | 294 assertions | `[AUTOMATED_TEST]` | Assertions actually executed during the run |
| **Assertions Passed** | 294 assertions | `[AUTOMATED_TEST]` | Successfully verified assertions |
| **Assertions Skipped** | 0 assertions | `[AUTOMATED_TEST]` | Skipped assertions (Strict gate: must be 0) |
| **Synthetic Pass Rate** | **100.0%** | `[AUTOMATED_TEST]` | Automated synthetic fixture success rate |
| **Harness Duration** | 17.7 seconds | `[AUTOMATED_TEST]` | Total runtime of the async test client |
| **In-Process p50 Latency** | 97.7 ms | `[AUTOMATED_TEST]` | Median in-process ASGI request latency |
| **In-Process p95 Latency** | 358.3 ms | `[AUTOMATED_TEST]` | 95th percentile in-process latency |
| **In-Process p99 Latency** | 467.1 ms | `[AUTOMATED_TEST]` | 99th percentile in-process latency |

---

## 2. Synthetic Scenario Coverage & Assertion Breakdown

Each synthetic fixture exercises specific core capabilities and boundary conditions:

| Task # | Evaluated Scenario | Fixture Sample | Assertions Exercised | Result |
| :-: | :--- | :--- | :-: | :-: |
| **Task 1** | Registration, Login & DPDP Consent Acceptance | SF01 - SF20 (All) | 40 assertions | **PASS** |
| **Task 2** | Conversation Lifecycle (Start, Resume & Versioning) | SF01 - SF20 (All) | 20 assertions | **PASS** |
| **Task 3** | Kannada Audio Ingestion & Mock ASR Bridge | SF01 - SF20 (All) | 20 assertions | **PASS** |
| **Task 4** | District & Taluk Entity Extraction & Normalization | SF01 - SF20 (All) | 20 assertions | **PASS** |
| **Task 5** | Canonical Crop Identification across Dialects | SF01 - SF20 (All) | 20 assertions | **PASS** |
| **Task 6** | Land Area (Acreage) & Ownership Type Extraction | SF01 - SF20 (All) | 20 assertions | **PASS** |
| **Task 7** | Spoken Correction & Negative Fact Overwrite | SF01, SF06, SF11, SF16 | 8 assertions | **PASS** |
| **Task 8** | Deterministic Scheme Recommendation & Legal Invariants | SF01 - SF20 (All) | 80 assertions | **PASS** |
| **Task 9** | Authenticated Audio Response Retrieval (Owner Bound) | SF01 - SF20 (All) | 20 assertions | **PASS** |
| **Task 10** | Simulated Network Dropout & Idempotent Resubmission | SF02, SF07, SF12, SF17, SF20 | 5 assertions | **PASS** |
| **Task 11** | Privacy Data Export & Verified DPDP Account Erasure | SF01 - SF20 Export, SF20 Delete | 22 assertions | **PASS** |

---

## 3. Scheme Governance & Statutory Invariants Verified

- **PM-KISAN Official Verification Gating:** Verified that all self-reported landowners match with mandatory caveat (`official_verification_required: true`).
- **Tenant Farmer Exclusion:** Verified that tenant fixtures (SF03, SF08, SF16) are deterministically excluded from owner-restricted schemes and routed to credit assistance.
- **PMFBY Seasonal Caveat:** Verified that crop insurance inquiries are gated with seasonal notification requirements.
- **Synthetic Demo Isolation:** Verified that `DEMO_MICRO_IRRIGATION` is strictly labeled `classification: SYNTHETIC_DEMO` and `demo_only: true`.

---

## 4. Harness Audit Artifacts & Checksums

- Metrics Artifact: `docs/m8_automated_validation_metrics.json`  
- Metrics SHA-256 Checksum: `64a732ce23dcbb26d55d0467971555516593f585c79a1aea746c29586ff08d40`  
- Harness Script: `scripts/run_pilot_field_trial.py`  
- Commit Reference: `2213d11eceecaaa7ec4ed14e24766de8833c36a0`  