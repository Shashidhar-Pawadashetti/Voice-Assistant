# 19 — Glossary and Primary References

## 1. Glossary

| Term | Meaning |
|---|---|
| ASR | Automatic Speech Recognition; audio to text |
| TTS | Text-to-Speech; text to generated audio |
| NLU | Natural Language Understanding; intent and entity extraction |
| LLM | Large Language Model |
| Slot | A typed fact needed for dialogue or rule evaluation, e.g. crop/area |
| Slot filling | Asking for and validating missing facts over conversation turns |
| Provenance | Where a fact came from and how it was verified |
| Three-valued logic | Rule condition result is TRUE, FALSE or UNKNOWN |
| BOLA/IDOR | Broken Object Level Authorization / Insecure Direct Object Reference |
| Idempotency | Retrying the same request does not create duplicate side effects |
| PWA | Progressive Web App |
| WER | Word Error Rate |
| CER | Character Error Rate |
| p95 latency | 95th percentile response time |
| Synthetic/demo scheme | Fictional test path that must never be represented as a government entitlement |

## 2. Primary technical references

### IndicConformer ASR

- Repository: https://github.com/AI4Bharat/IndicConformerASR
- AI4Bharat model page: https://ai4bharat.iitm.ac.in/areas/model/ASR/IndicConformer/
- Repository lists Kannada checkpoint (`kn`) and MIT licence for project code. Verify checkpoint/model terms and exact dependency instructions.

### Indic-TTS

- Repository: https://github.com/AI4Bharat/Indic-TTS
- Inference README: https://github.com/AI4Bharat/Indic-TTS/blob/master/inference/README.md
- Repository lists Kannada and a visible MIT code licence. Verify exact downloaded Kannada checkpoint and related asset terms separately.

### Qwen3 4B

- Model card: https://huggingface.co/Qwen/Qwen3-4B
- Qwen3 multilingual support description: https://qwenlm.github.io/blog/qwen3/
- Ollama model library: https://ollama.com/library/qwen3:4b
- Model card identifies Apache-2.0. Published Qwen3 language list includes Kannada. Model quality for this product must still be tested locally.

### Ollama structured output

- API documentation: https://github.com/ollama/ollama/blob/main/docs/api.md
- Structured outputs accept a JSON Schema in `format`; still validate locally with Pydantic.

### Faster-Whisper candidate

- Repository: https://github.com/SYSTRAN/faster-whisper
- Treat as candidate only until Kannada-specific quality is evaluated.

### PostgreSQL

- Version support: https://www.postgresql.org/support/versioning/
- PostgreSQL FAQ: https://www.postgresql.org/about/press/faq/

### Valkey / RabbitMQ

- Valkey repository/licence: https://github.com/valkey-io/valkey
- Valkey docs: https://valkey.io/docs/topics/introduction/
- RabbitMQ server licence: https://github.com/rabbitmq/rabbitmq-server/blob/main/LICENSE

### Government scheme sources

- PM-KISAN official portal: https://pmkisan.gov.in/
- PMFBY official portal: https://pmfby.gov.in/
- A portal home page is not enough to encode detailed rule conditions; record the exact current guidelines/notification and effective season.

### India data protection sources

- Digital Personal Data Protection Act / official Gazette search: https://egazette.gov.in/
- DPDP Rules 2025 notification (Gazette notification dated 13 November 2025): https://egazette.gov.in/WriteReadData/2025/267647.pdf
- MeitY/PIB explanation: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190014&lang=2&reg=3
- The Gazette commencement schedule is controlling for dates: the notification distinguishes provisions commencing on 13 November 2025, one year later (13 November 2026), and eighteen months later (13 May 2027). As of 30 October 2026, the one-year date is still in the future. Obtain legal review before production.

## 3. Reference verification date

This reference list was checked on **30 October 2026**. Re-check model versions, package compatibility, licensing, government notifications and statutory commencement dates immediately before deployment. Do not pin an unverified “latest” version just because a documentation page has changed.
