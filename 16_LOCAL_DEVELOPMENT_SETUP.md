# 16 — Local Development Setup

## 1. Target development environment

The project owner uses Windows. Use Windows PowerShell for the main Python/FastAPI development loop. Use WSL2 Ubuntu for ML model stacks when Linux/GPU dependency compatibility makes native Windows difficult. Keep ASR and TTS model environments isolated from the API environment.

## 2. Prerequisites

- Git;
- Python 3.11+ for API (pin exact patch in lock file);
- Docker Desktop with WSL2 backend, or PostgreSQL installed locally;
- Ollama for local Qwen3 inference;
- WSL2 Ubuntu for IndicConformer/Indic-TTS dependencies;
- FFmpeg available to the audio processing service;
- GPU drivers/runtime only if using GPU; CPU mode may be slower.

Do not assume a particular GPU or VRAM. Detect and document actual hardware before model performance testing.

## 3. API environment (PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

The agent should create `pyproject.toml` and a reproducible lock file rather than depending on unpinned ad-hoc installs. Baseline packages include:

- `fastapi`
- `uvicorn[standard]`
- `pydantic>=2`
- `pydantic-settings`
- `sqlalchemy>=2`
- `psycopg[binary]`
- `alembic`
- `httpx`
- `tenacity`
- `python-multipart`
- maintained Argon2 library
- `pytest`, `pytest-asyncio`, `httpx` test client
- formatter/linter/type checker selected by repository standards

Install exact compatible versions after model/runtime stack compatibility checks; lock them.

## 4. Ollama / Qwen3

Install from https://ollama.com/download, then:

```powershell
ollama pull qwen3:4b
ollama run qwen3:4b
```

Default local API base: `http://127.0.0.1:11434`.

Test a Kannada prompt and a structured extraction response. Use Ollama's JSON Schema `format` parameter with a Pydantic-generated schema where supported. Do not assume output quality from a single manual prompt; run the evaluation fixtures.

Do not expose the Ollama port publicly. Keep model ID and endpoint in environment config.

## 5. PostgreSQL

Use a currently supported major version. PostgreSQL 18 is listed as supported as of 30 October 2026; pin the chosen image tag and update policy. Local Compose is recommended.

Example connection string placeholder:

```text
postgresql+psycopg://krishi_app:CHANGE_ME@localhost:5432/krishi_mitra
```

Never use this placeholder as a production secret.

## 6. IndicConformer ASR (WSL2)

Official project: https://github.com/AI4Bharat/IndicConformerASR

The repository's documented setup points to AI4Bharat NeMo and a `nemo-v2` branch. Start from its current README and checkpoint-specific instructions; do not copy stale dependency pins blindly.

Typical repository bootstrap from their documented path:

```bash
git clone https://github.com/AI4Bharat/NeMo.git
cd NeMo
git checkout nemo-v2
bash reinstall.sh
```

Create a separate environment first. Verify PyTorch/CUDA compatibility, checkpoint hash and audio sample-rate expectation from model config. Run one supplied sample before integrating with FastAPI.

## 7. Indic-TTS (WSL2)

Official project: https://github.com/AI4Bharat/Indic-TTS

Consult its `inference/README.md`, requirements and model download instructions. It documents Kannada among supported languages and an inference server example. Isolate its Python environment, install the documented audio dependencies and verify the exact Kannada checkpoint's usage terms before sharing/deploying weights.

If the environment is incompatible with the API environment, keep TTS as a separate local service rather than forcing conflicting dependencies into one venv.

## 8. Environment file

Create `.env.example` with placeholders only:

```dotenv
APP_ENV=local
APP_SECRET_KEY=replace-me
DATABASE_URL=postgresql+psycopg://...
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:4b
ASR_PROVIDER=indicconformer
ASR_BASE_URL=http://127.0.0.1:8001
TTS_PROVIDER=indic_tts
TTS_BASE_URL=http://127.0.0.1:8002
AUDIO_TEMP_DIR=./.runtime/audio
AUDIO_MAX_BYTES=15728640
AUDIO_MAX_SECONDS=60
AUDIO_RESPONSE_TTL_SECONDS=600
```

Add real `.env` and `.runtime/` to `.gitignore`.

## 9. Local smoke test

The agent must implement and document commands equivalent to:

```powershell
# API
uvicorn app.main:app --reload

# Tests
pytest -q

# Health
Invoke-RestMethod http://127.0.0.1:8000/health/live

# Ollama check
ollama list
```

Do not document an ASR/TTS command until it is confirmed against the exact current repository/checkpoint version.

## 10. Hardware report

Before making capacity claims, record:

- OS and WSL version;
- CPU model/core count;
- RAM;
- GPU model and VRAM;
- driver/CUDA version if applicable;
- model quantization and checksum;
- concurrent worker count;
- benchmark audio length/sample rate.
