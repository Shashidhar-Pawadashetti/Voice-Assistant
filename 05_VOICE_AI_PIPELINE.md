# 05 — Voice and Language AI Pipeline

## 1. Pipeline responsibilities

The speech stack and language stack are separate. ASR produces text; NLU produces typed facts; dialogue code controls the conversation; the scheme engine computes recommendations; TTS speaks the final text.

```text
Audio -> Validate/Normalize -> ASR -> Transcript
Transcript + known context -> LLM NLU -> JSON -> Pydantic + semantic validation
Validated facts -> Normalizer -> Dialogue manager
Dialogue result -> Grounded response text -> TTS -> temporary audio
```

## 2. Audio input contract

- Initial accepted browser container: WAV/WEBM/OGG where supported by the chosen frontend browser; backend must inspect actual media and not trust filename/MIME alone.
- Normalize using FFmpeg to mono, 16 kHz PCM WAV if that is what the selected IndicConformer checkpoint expects. Confirm exact model expectation from its code/config; do not assume sample rate without inspecting checkpoint instructions.
- Enforce configurable upload bytes, duration and decoded-frame limits. Suggested initial caps: 15 MB and 60 seconds; adjust after testing.
- Reject zero-byte, unsupported, corrupt, excessively long or suspicious files.
- Do not execute uploaded files or trust embedded metadata.
- Store temporary audio outside the public web root with randomized server-generated filenames and restrictive permissions.
- Always delete temporary audio in `finally`; add periodic orphan cleanup for process crashes.

## 3. ASR adapter interface

Implement an interface similar to:

```python
class SpeechRecognizer(Protocol):
    async def transcribe(self, audio_path: Path, *, language: str = "kn") -> ASRResult: ...
```

`ASRResult` should include:

- `text`: transcript in native script where model provides it;
- `language`: `kn` or detected value;
- `provider` and `model_version`;
- `duration_ms`;
- `segments` if available;
- `confidence` only if the model provides a meaningful documented value;
- `warnings`: e.g. clipping, silence, low signal.

Never fabricate a numeric confidence score where the model does not provide a calibrated one.

### Primary candidate

AI4Bharat IndicConformer Kannada checkpoint. Repository: https://github.com/AI4Bharat/IndicConformerASR. It lists Kannada (`kn`) and MIT for the project. Its installation depends on AI4Bharat NeMo. Validate the checkpoint hash and exact usage/license terms.

### Fallback candidate

Faster-Whisper, repository: https://github.com/SYSTRAN/faster-whisper. It is a potential multilingual comparison. Do not automatically fallback to it for all ASR errors until Kannada accuracy is benchmarked against the same audio set. For MVP, safe fallback is asking the farmer to repeat, speaking more slowly, or switching to text input.

## 4. Kannada normalization layer

Maintain curated, versioned dictionaries:

- crop aliases and local names;
- district/taluk/village aliases;
- land measurement terms and numeric phrases;
- irrigation vocabulary;
- crop seasons;
- assistance categories;
- Kannada-English code-mixed phrases.

Normalization must be conservative:

1. preserve source transcript while retention policy permits;
2. map only known aliases to canonical IDs;
3. keep `raw_value`, `canonical_value`, `normalizer_version` and provenance;
4. do not silently infer a crop/location from an ambiguous word;
5. ask a farmer to confirm critical fields.

Examples are test fixtures, not a complete agricultural dictionary:

| Spoken phrase | Candidate canonical value |
|---|---|
| ಹನಿ ನೀರಾವರಿ / ಡ್ರಿಪ್ | `DRIP` |
| ತುಂತುರು ನೀರಾವರಿ | `SPRINKLER` |
| ಜೋಳ | configured sorghum crop code |
| ರಾಗಿ | configured finger millet crop code |
| ಎಕರೆ | `ACRE` |
| ಗುಂಟೆ | `GUNTA` |

Place names and crop names require a reviewed canonical dataset. Do not guess village/taluk matches from approximate spelling.

## 5. LLM adapter

Implement a provider-neutral `LanguageModel` interface; Ollama is the first adapter.

- Model ID from configuration (initial candidate `qwen3:4b`).
- Local endpoint default `http://127.0.0.1:11434`; never expose to internet.
- Use non-streaming structured JSON for slot extraction to avoid partial state updates.
- Provide a Pydantic-derived JSON Schema using Ollama `format` when supported.
- Keep temperature low for extraction; set bounded context and output tokens.
- Record provider/model/version, latency and validation outcome, not raw farmer content in metrics/logs.
- Timeouts and one bounded retry only. On invalid output, ask for clarification; do not endlessly retry.

### Extraction output schema (conceptual)

```json
{
  "intent": "FIND_SCHEMES",
  "entities": [
    {
      "slot": "district",
      "raw_value": "ಧಾರವಾಡ",
      "canonical_value": "DHAWAD",
      "value_type": "string",
      "assertion": "USER_STATED",
      "requires_confirmation": true
    }
  ],
  "correction_target": null,
  "unresolved_phrases": [],
  "assistant_language": "kn"
}
```

Do not let the model choose a scheme outcome or set `verified=true`. Model output is only a proposal for the application to validate.

## 6. Prompt rules

System instructions for extraction must explicitly say:

- Extract only facts actually stated or unambiguously implied by the current utterance and supplied trusted context.
- Do not assume land ownership from land possession/area.
- Do not convert a tenant into an owner.
- Do not infer eKYC, official registration, insurance enrolment or land-record verification.
- Distinguish a correction from a new fact.
- Return `UNKNOWN`/empty for missing data.
- Never decide scheme eligibility or calculate entitlement.
- Return only schema-conforming JSON.

Response-generation prompt must receive only typed dialogue action and trusted catalogue content. It must not browse, invent URLs, benefits, amounts, application deadlines or eligibility conditions.

## 7. TTS adapter

Interface:

```python
class SpeechSynthesizer(Protocol):
    async def synthesize(self, text: str, *, language: str = "kn") -> TTSResult: ...
```

- Evaluate AI4Bharat Indic-TTS Kannada.
- The project repo lists Kannada and publishes an MIT code licence; independently verify the exact downloaded checkpoint, voice assets and dataset licence/terms.
- Prefer a separately isolated TTS environment/process because ML dependencies may conflict with API and ASR dependencies.
- Store generated audio in a private temporary directory, serve only to the authorized conversation owner, and expire it quickly (initial default TTL 10 minutes).
- Never generate audio from untrusted HTML or execute text as code.
- TTS is best effort; a valid text response is still a successful assistant turn if speech synthesis fails.

## 8. Critical number handling

For area, crop, location, season and amounts:

- parse a candidate value;
- normalize it deterministically;
- repeat it back in Kannada;
- require confirmation before applying rules if extraction is ambiguous or high-impact;
- retain both original unit/value and normalized value;
- if the farmer corrects it, replace the active value and invalidate affected recommendation runs.

## 9. Quality gates

Before enabling voice as the default:

- benchmark with native Kannada speakers from multiple regions;
- measure WER and CER on held-out audio;
- measure slot-level exact-match/F1 for district, crop, area, season and ownership;
- compare clean, noisy, slow, fast and code-mixed speech;
- have speakers judge TTS intelligibility and naturalness;
- keep a text correction path for every voice turn.
