# 00 — Execution Order and Document Precedence

## Authority

These documents are the product and engineering source of truth for the Krishi Mitra AI/backend subsystem, as of 30 October 2026.

Precedence when two statements appear inconsistent:

1. Explicit safety/privacy rule in `11_SECURITY_AND_PRIVACY.md`.
2. Scheme truth and governance rule in `07_SCHEME_ENGINE_AND_GOVERNANCE.md` and `08_SCHEME_CATALOG_SEED.md`.
3. API and persisted-data contracts in `09_API_CONTRACT.md` and `10_DATA_MODEL.md`.
4. Architecture decisions in `04_ARCHITECTURE_DECISIONS.md`.
5. Functional behaviour in `02_PRODUCT_REQUIREMENTS.md` and `06_DIALOGUE_AND_MEMORY.md`.
6. Implementation examples in the remaining documents.

If the conflict cannot be resolved by precedence, stop that work item, document the ambiguity in `18_OPEN_QUESTIONS_AND_RISKS.md`, and ask the project owner. Do not make a consequential assumption silently.

## Required agent workflow

1. Inspect the existing repository and report its current structure, language, dependency manager, existing tests, branch and uncommitted changes. Do not overwrite existing user work.
2. Read this document set completely.
3. Create an implementation plan mapped to milestones M0–M7 in `15_IMPLEMENTATION_PLAN.md`.
4. Implement only M0.1 and M0.2 first: backend foundation and local LLM adapter/structured extraction. Keep the code runnable.
5. Run formatter, static checks, unit tests and smoke tests. Report exact commands and outcomes.
6. Present a concise milestone report and list blockers before moving to the next milestone.
7. Implement later milestones in dependency order. Each milestone must include tests and an updated README/configuration/example.
8. Do not claim a feature is implemented merely because a stub, interface or TODO exists.
9. Do not claim model quality, security, privacy compliance, high availability or load capacity without tests/evidence.

## Repository preservation

- If the repo already exists, follow its conventions where they do not violate a locked requirement.
- Do not delete or rewrite existing unrelated files.
- Never reset, force-push, or rewrite git history.
- Never commit `.env`, model weights, farmer audio, transcripts from real people, database dumps or secrets.
- If there are pre-existing changes, preserve them and mention them in the report.

## Required output after each milestone

- Implemented files/modules.
- API/schema changes.
- Database migrations, if any.
- Test files and exact test results.
- Local run instructions updated.
- Known limitations and unresolved decisions.
- Git diff summary; do not commit unless explicitly authorized.

## Mandatory stop conditions

Stop and ask the project owner before:

- adding an external hosted LLM/STT/TTS API;
- changing the primary language or model family;
- changing the data-retention policy;
- introducing an admin role, admin dashboard or public scheme-mutation endpoint;
- changing the meaning of recommendation statuses;
- writing factual real-scheme criteria without official evidence;
- collecting Aadhaar, bank, land-document or biometric/voiceprint data;
- claiming 1,000 concurrent inference capacity;
- adding a dependency with a licence incompatible with the project's intended use.

## Definition of done

A milestone is complete only when its acceptance criteria in `15_IMPLEMENTATION_PLAN.md` and `14_TEST_AND_EVALUATION.md` pass, relevant documentation is updated, and failures/limitations are reported honestly.
