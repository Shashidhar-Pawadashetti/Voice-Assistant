# 10 — PostgreSQL Data Model

## 1. General rules

- PostgreSQL is the system of record.
- Use UUID primary keys.
- Use UTC `timestamptz` for persisted times.
- Use migrations (Alembic); never rely on `create_all()` as production schema management.
- Add `farmer_id` to farmer-owned records and enforce it in repository/service queries.
- Use foreign keys and appropriate cascade/restrict semantics.
- Avoid storing raw audio.
- Avoid wide JSON blobs for core relational relationships; JSONB is acceptable for slot facts, rule trace detail and versioned metadata.

## 2. Tables

### `farmers`

- `id UUID PK`
- `phone_number_encrypted` or safely protected identifier; store a normalized search hash separately if needed
- `password_hash` (Argon2id)
- `preferred_language` default `kn`
- `account_status` (`ACTIVE`, `LOCKED`, `DELETION_PENDING`, `DELETED`)
- `created_at`, `updated_at`, `last_login_at`
- consent version/records should be in dedicated consent table

Never store password plaintext or OTP secrets. Decide phone encryption/index approach before adding production registrations.

### `farmer_profiles`

- `id UUID PK`
- `farmer_id UUID FK UNIQUE`
- `profile_data JSONB` or normalized child slot rows
- `profile_version BIGINT`
- `updated_at`

Use structured typed fields/tables for frequently queried values. JSONB is acceptable for extensible low-volume data but must have Pydantic schema validation.

### `conversations`

- `id UUID PK`
- `farmer_id UUID FK INDEX`
- `status` (`ACTIVE`, `PAUSED`, `COMPLETED`, `DELETED`)
- `state` dialogue enum
- `language`
- `summary` nullable text (only if retention consent permits)
- `version BIGINT` optimistic concurrency counter
- `created_at`, `updated_at`, `last_activity_at`

### `conversation_turns`

- `id UUID PK`
- `conversation_id UUID FK`
- `farmer_id UUID FK`
- `turn_number BIGINT`
- `role` (`FARMER`, `ASSISTANT`, `SYSTEM_EVENT`)
- `input_mode` (`VOICE`, `TEXT`, `NONE`)
- `transcript_text` nullable (only where permitted)
- `assistant_text` nullable
- `asr_model_version` nullable
- `llm_model_version` nullable
- `tts_model_version` nullable
- `status`
- `created_at`, `completed_at`
- unique `(conversation_id, turn_number)`

No audio binary or public filesystem path belongs here.

*(Implemented and verified with active persistence and optimistic version locking in Milestone M3).*

### `conversation_slots`

- `id UUID PK`
- `conversation_id UUID FK`
- `farmer_id UUID FK`
- `slot_key`
- `raw_value` nullable (retention policy applies)
- `canonical_value JSONB`
- `canonical_unit` nullable
- `slot_status`
- `provenance`
- `source_turn_id UUID FK nullable`
- `normalizer_version`
- `slot_version`
- `updated_at`
- unique `(conversation_id, slot_key, slot_version)`

Keep history of changed values only as long as necessary; do not retain unnecessary raw personal content.

### `consent_records`

- `id UUID PK`
- `farmer_id UUID FK`
- `purpose` (`ACCOUNT`, `CONVERSATION_HISTORY`, `TRANSCRIPT_RETENTION`, `VOICE_PROCESSING`)
- `notice_version`
- `status` (`GRANTED`, `WITHDRAWN`)
- `granted_at`, `withdrawn_at`
- `evidence_metadata` minimal

Do not bundle unrelated purposes into one unchecked consent.

### `jobs`

- `id UUID PK` (request ID)
- `farmer_id UUID FK`
- `conversation_id UUID FK`
- `turn_id UUID FK`
- `idempotency_key_hash`
- `payload_hash`
- `status`
- `attempt_count`
- `worker_type`
- `error_code` safe enum
- `created_at`, `started_at`, `completed_at`, `next_retry_at`
- unique `(farmer_id, idempotency_key_hash)`

Do not store uploaded audio bytes in job payload. Job payload can reference a temporary file only while valid and only through private storage metadata.

### `schemes`

- `id UUID PK`
- `scheme_id TEXT UNIQUE`
- `classification`
- `display_name`
- `assistance_category`
- `government_level`
- `active`

### `scheme_rule_versions`

- `id UUID PK`
- `scheme_id FK`
- `rule_version`
- `definition JSONB`
- `definition_hash`
- `verification_status`
- `effective_from`, `effective_to`
- `last_verified_at`, `review_due_at`
- `created_at`
- unique `(scheme_id, rule_version)`

Rule versions are immutable after release. New rules create a new row/version.

### `recommendation_runs`

- `id UUID PK`
- `farmer_id UUID FK`
- `conversation_id UUID FK`
- `profile_snapshot JSONB` (minimum necessary facts)
- `scheme_rule_version_id UUID FK`
- `evaluator_version`
- `outcome`
- `explanation_trace JSONB`
- `evaluated_at`

Retain only what is needed for transparency and user history.

### `deletion_requests`

- `id UUID PK`
- `farmer_id UUID FK` nullable after anonymization
- `status`
- `requested_at`, `completed_at`
- `result_summary` non-sensitive

### `audit_events`

- `id UUID PK`
- `actor_type` (`FARMER`, `SYSTEM`)
- `actor_id` nullable
- `event_type`
- `resource_type`, `resource_id`
- `created_at`
- `metadata` restricted to non-sensitive fields

No transcript, audio, password, token, Aadhaar or bank data in audit metadata.

## 3. Required indexes

- `conversations(farmer_id, last_activity_at DESC)`
- `conversation_turns(conversation_id, turn_number)`
- `conversation_slots(conversation_id, slot_key, slot_version DESC)`
- `jobs(status, created_at)`
- `recommendation_runs(conversation_id, evaluated_at DESC)`
- indexes on unique IDs and foreign keys used for authorization queries

## 4. Authorization query rule

Never do:

```sql
SELECT * FROM conversations WHERE id = :conversation_id;
```

Do:

```sql
SELECT * FROM conversations
WHERE id = :conversation_id
  AND farmer_id = :authenticated_farmer_id;
```

Apply the same principle to turns, jobs, recommendations and audio response metadata.

## 5. Transaction boundaries

For a completed turn, persist as one consistent transaction where practical:

- turn status/transcript/assistant text;
- slot state/version;
- conversation state/version;
- recommendation run/trace when performed;
- job status/result reference.

Do not mark a job completed before its result is committed.

## 6. Deletion semantics

Create and test a dependency map. Deletion must address farmer account/profile, conversations, turns, slot facts, recommendation runs, job records, audio response files, cache keys, temporary files and backups according to policy. Some minimal legally/operationally required security records may need restricted retention; this requires legal review and must not retain conversation content by default.
