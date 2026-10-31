# Krishi Mitra — Milestone M8: Automated Synthetic Cohort Simulation Report

**Execution Date:** 2026-10-31  
**Status:** Certified Automated Regression Run  
**Evidence Classification:** `AUTOMATED_TEST` (In-process ASGI simulation using synthetic test fixtures)  
**Execution Harness:** `scripts/run_pilot_field_trial.py`  
**Raw Metrics Source:** `docs/m8_automated_validation_metrics.json`  
**Software Version:** 1.0.0 | **Commit SHA:** `2213d11eceecaaa7ec4ed14e24766de8833c36a0`  
**Harness Checksum (SHA-256):** `a8afc8965163b2e070ea689c2964542f7391a04908a64c47093eab078fa09f36`  

---

> [!IMPORTANT]
> **EVIDENCE INTEGRITY DISCLOSURE:**  
> **This report documents an automated simulation executed by an in-process test runner. Zero real human farmers participated in this run.**  
> - The 20 evaluated profiles are **synthetic test fixtures (`SF01`–`SF20`)** designed as automated test vectors across 4 Karnataka agro-climatic clusters.
> - The reported latencies (median 81.7 ms) represent **in-process ASGI HTTP client request duration** inside a Python runtime, **not** real-world rural cellular (2G/3G/4G) wireless transmission delay.
> - ASR and TTS operations in this harness utilized deterministic mock interfaces (`MockSpeechRecognizer` and `MockSpeechSynthesizer`).
> - The 100.0% completion rate reflects **software invariant compliance**, not human usability completion.
> - Real-world farmer usability is governed separately by [`M8_REAL_FIELD_PILOT_PROTOCOL.md`](file:///C:/Users/shash/OneDrive/Desktop/PROJECTS/Voice-Assistant/docs/M8_REAL_FIELD_PILOT_PROTOCOL.md).

---

## 1. Executive Summary & Automated Execution Metrics

The M8 automated validation harness exercised the Krishi Mitra voice-first platform across **20 predefined synthetic fixture personas** covering **11 standardized pipeline capabilities**.

### Automated Simulation Summary
- **Evaluation Mode:** Automated In-Process ASGI Test Execution (`httpx.AsyncClient` + `ASGITransport`).
- **Total Synthetic Fixtures Evaluated:** 20 (`SF01` to `SF20`).
- **Total Scenario Assertions Required:** 294 assertions.
- **Total Scenario Assertions Exercised:** 294 assertions.
- **Assertions Passed:** **294 / 294 (100.0%)**.
- **Assertions Failed:** **0 (0.0%)**.
- **Assertions Skipped:** **0 (0.0%)** (Strict zero-skip policy enforced).
- **Harness Total Execution Time:** 13.02 seconds.
- **In-Process ASGI Request Latency Profile:**
  - **p50 (Median):** **81.7 ms**
  - **p95:** **198.7 ms**
  - **p99:** **229.5 ms**
  - **Mean:** **81.2 ms**
  - **Min / Max:** 36.1 ms / 232.0 ms

---

## 2. Standardized Task Assertion Performance

All 11 automated tasks executed without failures across all 20 synthetic fixtures:

| Task # | Simulated Pipeline Capability | Assertion Type | Assertions Exercised | Passed | Failed | Success Rate | In-Process Latency (Mean) | Evidence Class |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Task 1** | Registration, Login & DPDP Consent Acceptance | Auth & Consent Invariants | 40 | 40 | 0 | **100.0%** | 86.4 ms | `AUTOMATED_TEST` |
| **Task 2** | Conversation Session Lifecycle (Create & Probe) | Session State Machine | 20 | 20 | 0 | **100.0%** | 74.2 ms | `AUTOMATED_TEST` |
| **Task 3** | Kannada Voice Recording Ingestion & Mock ASR Bridge | Audio Upload & Format | 20 | 20 | 0 | **100.0%** | 108.6 ms | `AUTOMATED_TEST` |
| **Task 4** | District & Taluk Extraction & Normalization | Geographic Canonicalization | 20 | 20 | 0 | **100.0%** | In text turn | `AUTOMATED_TEST` |
| **Task 5** | Crop Identification & Canonicalization | Agronomic Normalization | 20 | 20 | 0 | **100.0%** | In text turn | `AUTOMATED_TEST` |
| **Task 6** | Land Area (Acres/Guntas) & Ownership Extraction | Quantitative Extraction | 20 | 20 | 0 | **100.0%** | In text turn | `AUTOMATED_TEST` |
| **Task 7** | Spoken Correction & Slot Negation Handling | State Context Update | 4 | 4 | 0 | **100.0%** | 82.1 ms | `AUTOMATED_TEST` |
| **Task 8** | Scheme Rule Evaluation & Verification Caveats | Deterministic Scheme Logic | 80 | 80 | 0 | **100.0%** | 104.3 ms | `AUTOMATED_TEST` |
| **Task 9** | Authenticated Audio Retrieval & Ephemeral Storage | Ephemeral Store & BOLA | 20 | 20 | 0 | **100.0%** | 41.5 ms | `AUTOMATED_TEST` |
| **Task 10** | Simulated Network Interruption & Idempotent Resubmission | Network Retry Deduplication | 5 | 5 | 0 | **100.0%** | 78.9 ms | `AUTOMATED_TEST` |
| **Task 11** | Privacy Data Portability Export & Account Deletion | DPDP Statutory Erasure | 45 | 45 | 0 | **100.0%** | 84.7 ms | `AUTOMATED_TEST` |
| **TOTAL** | **Aggregate Automated Platform Invariants** | **End-to-End Regression** | **294** | **294** | **0** | **100.0%** | **Overall p50: 81.7 ms** | `AUTOMATED_TEST` |

---

## 3. Synthetic Fixture Cohort Breakdown & Scenario Coverage

The 20 synthetic fixtures test specific edge cases across 4 Karnataka agro-climatic clusters:

### 3.1 North Karnataka Cluster (Dryland / Irrigated Fixtures)
- **`SF01` (Dharwad, Navalgund):** Spoken fact correction scenario (2 acres updated to 3 acres green gram). Verified audit trail logging and profile preservation.
- **`SF02` (Belagavi, Bailhongal):** 5 acres sugarcane. Simulated network disconnection during turn submission; idempotent resubmission with duplicate `client_turn_id` verified zero state corruption.
- **`SF03` (Bagalkote, Badami):** 2 acres sorghum under **tenant farming (ಗೇಣಿ)**. Verified tenant exclusion: system strictly prevented PM-KISAN matching and routed to tenant credit.
- **`SF04` (Vijayapura, Indi):** 4 acres pigeon pea (tur) dryland priority scenario. Verified PM-KISAN owner qualification with mandatory official verification disclaimer.
- **`SF05` (Dharwad, Hubballi):** 1.5 acres groundnut marginal farmer scenario. Rapid multi-slot assembly verified.
- **`SF06` (Belagavi, Gokak):** 3.5 acres maize. Fractional acreage ("3.5 acres") canonicalization verified.

### 3.2 Kalyana Karnataka Cluster (Arid / Pulse Zone Fixtures)
- **`SF07` (Kalaburagi, Aland):** 6 acres pigeon pea drought damage scenario with network interruption simulation. Verified PMFBY gating requiring official crop-cutting experiment surveys.
- **`SF08` (Kalaburagi, Sedam):** 2.5 acres cotton tenant farmer scenario. Verified exclusion from capital asset schemes and tenant credit advice routing.
- **`SF09` (Raichur, Manvi):** 4 acres canal irrigated paddy. Canal irrigation subsidy matching verified.
- **`SF10` (Bidar, Humnabad):** 3 acres green gram pulse incentive matching verified.
- **`SF11` (Koppal, Kushtagi):** 2 acres finger millet (`FINGER_MILLET`) dryland scenario. Spoken correction from 1 to 3 acres verified.

### 3.3 South Karnataka Cluster (Wetland / Rainfed Fixtures)
- **`SF12` (Mandya, Maddur):** 2 acres sugarcane with network interruption simulation. Synthetic demonstration scheme (`DEMO_MICRO_IRRIGATION`) evaluated; verified explicit `DEMO_ONLY` badge.
- **`SF13` (Mysuru, T. Narasipura):** 1.5 acres paddy marginal holding scenario. Verified small-farmer threshold matching.
- **`SF14` (Hassan, Channarayapatna):** 3 acres finger millet rainfed scenario. Regional vocabulary canonicalization verified.
- **`SF15` (Mandya, Pandavapura):** 4 acres finger millet scenario. Taluk mapping verified.
- **`SF16` (Chamarajanagara, Kollegala):** 2.5 acres ragi tenant farmer scenario. Verified tenant exclusion and spoken correction handling.

### 3.4 Coastal Karnataka Cluster (Plantation / Coastal Paddy Fixtures)
- **`SF17` (Uttara Kannada, Sirsi):** 1.5 acres arecanut (`ARECANUT`) plantation with network interruption. Synthetic demo isolation verified.
- **`SF18` (Udupi, Karkala):** 2 acres coastal monsoon paddy scenario. Kharif cycle canonicalization verified.
- **`SF19` (Dakshina Kannada, Puttur):** 1 acre arecanut horticulture scenario. Verified plantation entity extraction.
- **`SF20` (Udupi, Kundapura):** 2.5 acres paddy with network drop and DPDP account erasure simulation. Verified complete cryptographic tombstoning, token revocation, and profile purge.

---

## 4. Key Statutory & Algorithmic Invariants Confirmed

1. **Zero LLM Eligibility Fabrication:**
   All 20 recommendations were computed strictly via deterministic Python AST rule engines (`app/core/scheme/engine.py`). Zero scheme recommendations were generated by unstructured generative LLM prompts.
2. **Mandatory Verification Caveats on Self-Reported Data:**
   Every recommendation generated under self-reported facts (`USER_STATED`) explicitly included the required verification caveat (`official_verification_required: true`).
3. **Statutory Tenant Exclusion:**
   Non-titleholding tenant farmers (`SF03`, `SF08`, `SF16`) were blocked from landowner-restricted schemes with 100% adherence.
4. **Idempotent Turn Processing:**
   Simulated duplicate turn submissions with identical `client_turn_id` returned identical cached turn responses without creating duplicate turns or triggering optimistic lock failures.
5. **DPDP Compliance Verification:**
   Account deletion scrubbed personal identifiers, revoked active sessions, and preserved only irreversibly anonymized audit counts.
