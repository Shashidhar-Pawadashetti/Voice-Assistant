# Milestone M1 — Speech Pipeline & Voice Orchestration

## 1. Overview

Milestone M1 delivers the end-to-end voice processing stack for Krishi Mitra:
1. **M1.1 (ASR):** Audio validation, normalization (16 kHz mono PCM WAV via FFmpeg), and AI4Bharat IndicConformer Kannada speech recognition adapter with transient lifecycle and zero raw audio persistence.
2. **M1.2 (TTS):** Preprocessing/sanitization, Kannada numeral expansion, AI4Bharat Indic-TTS speech synthesis adapter, ephemeral response storage (10-minute TTL), and text-only graceful fallback.
3. **M1.3 (Pipeline Orchestration):** Complete voice turn processing:
   $$\text{Audio Input} \rightarrow \text{Validate/Normalize} \rightarrow \text{ASR} \rightarrow \text{NLU Extractor} \rightarrow \text{Grounded Kannada Response} \rightarrow \text{TTS} \rightarrow \text{Ephemeral Audio URL}$$

---

## 2. Model Licensing & Provenance

### ASR: AI4Bharat IndicConformer (Kannada)
- **Repository:** https://github.com/AI4Bharat/IndicConformerASR
- **Code License:** MIT License.
- **Model Checkpoint:** `ai4bharat/indicconformer_asr_kn_v1` (Conformer CTC / Hybrid architecture trained on IndicSpeech and open audio datasets).
- **Weights License:** Creative Commons Attribution 4.0 International (CC-BY 4.0) / MIT.
- **Input Audio Contract:** Single-channel (mono), 16000 Hz sample rate, 16-bit signed PCM WAV (`pcm_s16le`).
- **Memory Footprint:** ~600 MB - 1.2 GB VRAM.

### TTS: AI4Bharat Indic-TTS (Kannada)
- **Repository:** https://github.com/AI4Bharat/Indic-TTS
- **Code License:** MIT License.
- **Model Checkpoints:** FastSpeech2 acoustic model + HiFi-GAN neural vocoder for Kannada (`ai4bharat/indic_tts_kn_v1`).
- **Weights License:** Creative Commons Attribution 4.0 International (CC-BY 4.0).
- **Output Audio Contract:** Playback-compatible 22.05 kHz or 16 kHz PCM WAV.
- **Memory Footprint:** ~800 MB - 1.5 GB VRAM.

---

## 3. Hardware Architecture & Isolation Strategy

### Limited GPU Memory (4 GB VRAM RTX 2050)
On a local development machine with an NVIDIA GeForce RTX 2050 (4 GB VRAM):
- Local Ollama `qwen3:4b` consumes ~2.5 GB VRAM.
- Concurrently loading NeMo IndicConformer (~1.2 GB) and Indic-TTS FastSpeech2 (~1.2 GB) into the same CUDA process would exceed the 4 GB limit, leading to CUDA Out-Of-Memory (OOM) crashes.
- Furthermore, NVIDIA NeMo relies on C++/CUDA Linux binaries not natively supported on Windows.

### Architectural Solution
1. **Isolated Microservice Topology:**
   IndicConformer and Indic-TTS run as isolated Python HTTP microservices (or within WSL2 / separate lightweight containers) with on-demand worker execution or CPU fallback (`device="cpu"`).
2. **Provider Abstraction & Factory Pattern:**
   `get_speech_recognizer()` and `get_speech_synthesizer()` instantiate either the production HTTP adapters (`IndicConformerAdapter`, `IndicTTSAdapter`) or local development mock providers (`MockSpeechRecognizer`, `MockSpeechSynthesizer`) controlled via environment settings (`ASR_PROVIDER=mock`, `TTS_PROVIDER=mock`).
3. **Subprocess Isolation for Normalization:**
   FFmpeg transcoding is executed inside worker threads via `asyncio.to_thread(subprocess.run, ...)` using direct argument vectors (no shell execution). This guarantees compatibility with `WindowsSelectorEventLoopPolicy` and shields the event loop from CPU-heavy decoding.

---

## 4. Benchmark & Quality Evaluation (CER / WER)

ASR accuracy is benchmarked using `jiwer` against reviewed reference Kannada farmer utterances across Karnataka dialect zones:

| Benchmark Utterance | Dialect Zone / Focus | Reference Spoken Kannada | Baseline Target WER | Baseline Target CER |
|---|---|---|---|---|
| `utt_001` | North Karnataka (Dharwad) | ಧಾರವಾಡ ಜಿಲ್ಲೆಯಲ್ಲಿ ಜೋಳ ಬೆಳೆಯಲು ಸಹಾಯಧನ ಬೇಕು | $\le 0.15$ | $\le 0.05$ |
| `utt_002` | Southern Karnataka (Mandya) | ನನಗೆ ಎರಡು ಎಕರೆ ಜಮೀನಿದೆ ಹನಿ ನೀರಾವರಿ ಸಬ್ಸಿಡಿ ಬೇಕಾಗಿದೆ | $\le 0.15$ | $\le 0.05$ |
| `utt_003` | Kalyana Karnataka (Kalaburagi) | ಕಲಬುರಗಿ ತಾಲೂಕು ತೊಗರಿ ಬೆಳೆ ಬರ ಪರಿಹಾರ ಯೋಜನೆ | $\le 0.18$ | $\le 0.06$ |
| `utt_004` | Code-Mixed Ag-English | ಬೆಳೆ ಇನ್ಶೂರೆನ್ಸ್ ಸ್ಟೇಟಸ್ ಚೆಕ್ ಮಾಡಬೇಕು | $\le 0.20$ | $\le 0.07$ |

*Simulated tests and live-model benchmark scripts are strictly partitioned in the test suite (`tests/unit/test_asr_evaluation.py`).*

---

## 5. Security & Privacy Invariants

1. **Transient Audio Only:** Uploaded audio is processed inside `transient_audio_file` context managers. Unconditional deletion in `finally` blocks ensures zero raw audio persistence.
2. **Path Traversal Protection:** Ephemeral audio IDs are validated with strict regex (`^[a-f0-9]{32}$`). Filenames are never taken from client uploads.
3. **No Audio or Transcripts in Logs:** Loggers explicitly scrub all transcripts, audio byte payloads, and PII. Access logs only record route, status, latency, and sanitized metadata.
4. **Best-Effort TTS Degradation:** If speech synthesis is unreachable or fails, the API turn succeeds with text output and `speech_available: false`. Conversation state is preserved.
5. **No LLM Eligibility Decisions:** The NLU layer extracts facts; deterministic Python rule evaluation (Milestone M4) is solely responsible for scheme eligibility decisions.
