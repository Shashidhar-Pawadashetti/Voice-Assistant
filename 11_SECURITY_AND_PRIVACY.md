# 11 — Security, Privacy and Identity

## 1. Privacy design principles

- purpose limitation;
- data minimization;
- clear notice and understandable consent;
- no raw input voice persistence by default;
- no third-party AI transfer in MVP;
- limited retention;
- protected account and farmer data;
- ability to access, correct and delete saved data through a documented workflow;
- no voiceprint/biometric authentication.

The DPDP Act, 2023 and DPDP Rules, 2025 have a phased commencement schedule. The official Gazette notification dated 13 November 2025 provides for some provisions to commence on publication (13 November 2025), specified provisions to commence one year later (13 November 2026), and most substantive processing/obligation provisions listed in the notification to commence eighteen months later (13 May 2027). As of 30 October 2026, the one-year tranche has not yet commenced, and the eighteen-month tranche is later still. The exact provisions are listed in the Gazette notification; do not infer that the entire Act became effective merely because the Rules were notified. Consult the Gazette schedule and obtain legal review before public production. Build the safeguards now rather than treating phased commencement as a reason to delay privacy controls.

## 2. Identity model — no admin

### Human identity: FARMER

- can register/authenticate;
- can access their own account, profile, conversations, turns, recommendations and ephemeral audio responses;
- can correct own profile and request data deletion;
- cannot access or mutate scheme definitions;
- cannot access another farmer's resources.

### Machine identity: SYSTEM

- internal service-to-service identity only;
- authenticates with separate service credentials, private network and/or mTLS;
- has narrowly scoped permissions for required operations;
- is not a role that can be selected by the browser;
- must not share farmer JWT secrets.

No admin role, admin dashboard or public scheme CRUD endpoints.

## 3. Authentication

For MVP, use a secure password-based flow tied to a normalized mobile identifier. The phone number is not verified unless a real OTP provider has been integrated. Do not claim phone ownership verification merely because a number was entered.

- Hash passwords with Argon2id using a maintained library and secure parameters.
- Use rate limiting and generic authentication failure messages.
- Access token short-lived (configurable; initial 10–15 minutes).
- Refresh token rotation and revocation.
- Prefer refresh token in HttpOnly, Secure, SameSite cookie; access token in browser memory.
- If cross-site frontend deployment requires `SameSite=None`, require Secure and implement CSRF protections.
- Never place access/refresh tokens in URLs or logs.
- Secret values only via environment/secret manager; `.env` ignored by git.
- Do not use default production credentials.

Phone OTP can be a production extension, but it needs an SMS provider and may not satisfy the all-free constraint. Keep authentication provider-neutral.

## 4. Authorization

- Derive `farmer_id` from validated access token, never request body/path ownership values.
- Every repository method for farmer-owned resources requires authenticated farmer ID.
- Return 404 for not found/unauthorized resource ownership where that avoids information leakage.
- Test IDOR/BOLA across every route.
- Use least-privilege PostgreSQL credentials.
- Worker service credentials are distinct from application/user credentials.
- Scheme data is read-only to normal API runtime.

## 5. Audio handling

- Input audio is untrusted binary data.
- enforce size, duration, codec and decoding limits;
- use server-generated filenames;
- store outside public static folder;
- prevent path traversal and shell injection;
- invoke FFmpeg with argument arrays, not shell-constructed strings;
- process in a restricted temporary directory/container;
- delete after inference in `finally`;
- run periodic cleanup for crash leftovers;
- do not place audio in exception messages, debug logs or backups;
- use a short TTL for generated response audio.

## 6. Transcript and conversation retention

Because conversation resume is a requirement, persist the minimum necessary structured slot data and conversation state. Retain full transcript/message text only if the relevant purpose is clearly disclosed and consented. Support retention configuration and deletion. Prefer short, structured, redacted state over full history.

A transcript can contain personal information even without a voice recording. Treat it as protected data.

## 7. Data not collected in MVP

Do not request or store:

- Aadhaar number or Aadhaar scan;
- bank account number/IFSC;
- land deed or other document uploads;
- voiceprint/biometric identity template;
- caste/religion/income/health data;
- precise GPS location;
- unnecessary contact list/device identifiers.

If a real scheme rule eventually requires a sensitive fact, stop and obtain project-owner/legal approval, document necessity and lawful basis, and design a separate secure collection flow. Do not add it opportunistically.

## 8. Encryption

- HTTPS/TLS for client-to-server and service-to-service connections.
- Encrypt database volumes and backups.
- Field-level encryption for phone identifiers or sensitive profile fields if stored.
- Store encryption keys outside the database and rotate them under documented operations.
- Restrict database backup access.

## 9. Logging and monitoring privacy

Allowed log fields: request ID, route template, status, duration, model ID/version, error code, queue time, turn ID where pseudonymous, and aggregate metrics.

Never log: audio, transcript, prompt, full LLM output, phone number, password, token, OTP, Aadhaar, bank information, raw profile JSON or SQL bind parameters containing user content.

Production error reporting must scrub request bodies and uploaded files.

## 10. Prompt injection and untrusted content

Farmer text and transcripts are untrusted data. They must not alter system rules or trigger tools. The LLM has no direct database, network, shell, file or scheme-rule write access. Scheme content is supplied by trusted application code as data, not instructions.

## 11. Deletion and correction

- Implement deletion as an authenticated workflow.
- delete linked database rows, cache entries and temporary/generated audio;
- invalidate refresh tokens and sessions;
- ensure queued jobs cannot re-create data after deletion (check account status before processing);
- record a minimal deletion status event without retaining deleted content;
- define backup expiry and restore-time deletion replay process.

## 12. Legal implementation note

The product team must obtain qualified legal advice for public deployment, including DPDP obligations, phased commencement dates, notices/consent language, grievance contact requirements, retention and children's data if minors may use the service. This technical document is not legal advice.
