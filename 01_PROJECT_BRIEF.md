# 01 — Project Brief

## 1. Product name

**Krishi Mitra** — a voice-first AI assistant that helps farmers in Karnataka discover potentially suitable government agricultural schemes through natural Kannada conversation.

## 2. Problem

Central and State Government support for farmers spans income assistance, crop insurance, irrigation, equipment and related services. Scheme information is distributed across portals and notifications, eligibility terminology is often formal, and many farmers are more comfortable speaking naturally than filling long forms. Regional accents, local crop names, Kannada-English code-mixing and uncertainty about technical terms make conventional search interfaces difficult.

## 3. Challenge statement

Build a voice-first AI assistant that understands farmers speaking naturally in Kannada, gathers agricultural information conversationally, and recommends potentially applicable schemes using transparent and verifiable eligibility rules.

## 4. Product objective

A farmer should be able to:

1. open the web application and start a voice conversation;
2. speak in natural Kannada, including common code-mixed words;
3. receive a faithful transcript/interpretation and correct misunderstandings;
4. provide relevant farm details over multiple turns rather than completing a long form;
5. ask follow-up questions without repeating already-confirmed details;
6. receive scheme suggestions with matched, failed and unknown conditions clearly explained;
7. hear the explanation in understandable Kannada;
8. resume a saved conversation, subject to consent and retention settings.

## 5. Intended users and roles

### Farmer

The only human application role. A farmer can access only their own profile, conversations, audio-response resources and recommendation history.

### System service identity

An internal non-human service identity for API-to-worker and trusted internal operations. It is not a user account and cannot log in through the farmer interface. It is authenticated by service credentials and/or private network controls.

### Explicitly excluded

There is no admin account, admin dashboard, public admin API or self-service editing of real scheme rules. Approved scheme catalog changes are delivered through reviewed, version-controlled code/data releases.

## 6. MVP scope

- Kannada speech-to-text using AI4Bharat IndicConformer.
- Text understanding and structured slot extraction with local Qwen3 4B via Ollama, subject to evaluation.
- Conversational slot filling and correction handling using a deterministic Python state machine.
- Kannada speech generation using AI4Bharat Indic-TTS after model-weight licence and runtime validation.
- Rule-engine framework with TRUE/FALSE/UNKNOWN conditions.
- Five reference scheme records: PM-KISAN, PMFBY, and three fictional demo schemes.
- PostgreSQL persistence of farmer profile, conversations, turns/slot values and recommendation traces, according to consent/retention rules.
- Farmer authentication and ownership authorization.
- Versioned REST API for a separate frontend.
- Basic retry/idempotency and recoverable asynchronous-job contract.
- Unit, integration, voice-quality and scheme-rule tests.

## 7. Non-goals for the hackathon MVP

- Applying for schemes on behalf of farmers.
- Guaranteeing eligibility, sanction, enrolment, claim acceptance or payment.
- Accessing government/private databases (FRUITS, land records, Aadhaar, bank systems) without an officially authorized integration and credentials.
- Collecting or validating Aadhaar or bank details.
- Fully offline ASR/LLM/TTS on the farmer's phone.
- Building or fine-tuning a new foundational ASR/LLM/TTS model.
- Supporting every Indian language; Kannada is the first-class language.
- Public admin interface or user-managed scheme-rule editing.
- A production SLA for 1,000 simultaneous speech inference jobs before appropriate hardware and load testing exist.

## 8. Product principle

**The core innovation is interaction quality.** Krishi Mitra must understand natural speech, preserve context, confirm important values, ask useful questions, recover from corrections and explain limitations. A simple microphone button over a generic chatbot does not meet the challenge.

## 9. User-facing disclaimer

The interface and spoken assistant must communicate, in simple Kannada and English where appropriate, that scheme results are preliminary information based on the details supplied; final eligibility and benefits are determined by the relevant government department/official scheme process. Fictional demo schemes must be explicitly labelled as demonstration-only and not real government benefits.
