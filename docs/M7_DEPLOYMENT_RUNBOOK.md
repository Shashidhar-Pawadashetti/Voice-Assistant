# M7 Production Deployment Runbook

**Project:** Krishi Mitra (ಕೃಷಿ ಮಿತ್ರ)  
**Document:** Production Operations & Deployment Runbook  
**Audience:** Platform Engineers, SREs, and Deployment Administrators  
**Version:** 1.0 (Milestone M7)  

---

## 1. System Overview & Deployment Architecture

Krishi Mitra is packaged as a lightweight, containerized stack composed of five primary containers:
1. **`reverse-proxy` (Nginx 1.27 Alpine):** Edge reverse proxy terminating TLS, managing rate-limit zones, proxy buffering, and payload size enforcement (15MB voice, 2MB general).
2. **`frontend` (Nginx Alpine):** Production web server serving the compiled React 18 TypeScript PWA application shell and caching assets.
3. **`api` (Python 3.11 Slim):** Multi-stage FastAPI ASGI application running under Uvicorn with non-root security context (`krishiuser`).
4. **`db` (PostgreSQL 16 Alpine):** Primary relational store with persistent Docker volume storage and health checks.
5. **`redis` (Redis 7 Alpine):** Distributed sliding-window rate limiter, token rotation coordinator, and JTI revocation store.

```
+-----------------------------------------------------------------------------------+
|                                  HOST MACHINE                                     |
|                                                                                   |
|   Port 80 / 443                                                                   |
|         │                                                                         |
|         ▼                                                                         |
|  [reverse-proxy] ──┬── / ─────────────► [frontend:80] (Static PWA)               |
|                    │                                                              |
|                    └── /api/, /health/ ─► [api:8000] (FastAPI ASGI)               |
|                                                │                                  |
|                                                ├──► [db:5432] (PostgreSQL 16)     |
|                                                ├──► [redis:6379] (Redis 7)        |
|                                                └──► host.docker.internal:11434    |
|                                                     (Ollama Local Inference)      |
+-----------------------------------------------------------------------------------+
```

---

## 2. Prerequisites & Environment Configuration

### 2.1 Host System Requirements
- **OS:** Ubuntu 22.04 LTS / Debian 12 / Rocky Linux 9 or Windows Server 2022 with Docker Desktop / WSL2.
- **Compute:** Minimum 4 vCPU, 8 GB RAM (16 GB RAM recommended for concurrent local LLM + speech inference).
- **Storage:** 50 GB NVMe SSD for Docker images, audio buffer, database volume, and backups.
- **Software Dependencies:**
  - Docker Engine $\ge$ 24.0
  - Docker Compose $\ge$ v2.20
  - OpenSSL (for certificate generation)
  - Python $\ge$ 3.11 (for host operations scripts)

### 2.2 Environment Variables (`.env`)
Create `/etc/krishi-mitra/.env` or `.env` in the repository root:

```ini
# Application Runtime
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
ENABLE_PUBLIC_DOCS=false

# Cryptographic Keys (MUST BE GENERATED AT DEPLOY TIME)
APP_SECRET_KEY=generate_with_openssl_rand_hex_32_min_32_chars
ENCRYPTION_KEY=generate_with_openssl_rand_base64_32
ENCRYPTION_KEY_PREVIOUS=
BLIND_INDEX_KEY=generate_with_openssl_rand_hex_32

# Database Configuration
DATABASE_URL=postgresql+psycopg://krishi_app:STRONG_POSTGRES_PASSWORD_HERE@db:5432/krishi_mitra
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_TIMEOUT_SECONDS=5.0

# Distributed Cache & Rate Limiting
REDIS_URL=redis://redis:6379/0

# Speech & LLM Configuration
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3:4b
AUDIO_TEMP_DIR=/app/.runtime/audio

# Network & Proxy Trust
MAX_UPLOAD_SIZE_BYTES=15728640
TRUSTED_PROXIES=127.0.0.1,nginx,reverse-proxy
CORS_ORIGINS=https://krishi-mitra.gov.in,https://app.krishi-mitra.local
```

> [!CAUTION]
> Never deploy with default or development keys. Generate keys using:
> ```bash
> openssl rand -hex 32  # For APP_SECRET_KEY & BLIND_INDEX_KEY
> openssl rand -base64 32  # For ENCRYPTION_KEY
> ```

---

## 3. Step-by-Step Deployment Procedure

### Step 1: Clone Repository & Prepare Directories
```bash
git clone https://github.com/Shashidhar-Pawadashetti/Voice-Assistant.git /opt/krishi-mitra
cd /opt/krishi-mitra

# Create local runtime and backup directories
mkdir -p .runtime/audio backups nginx/ssl
chmod 700 .runtime/audio backups
```

### Step 2: Configure TLS Certificates
For production deployments using Let's Encrypt or state agency wildcard certificates:
```bash
# Place fullchain and private key in nginx/ssl/
cp /etc/letsencrypt/live/krishi-mitra.gov.in/fullchain.pem nginx/ssl/fullchain.pem
cp /etc/letsencrypt/live/krishi-mitra.gov.in/privkey.pem nginx/ssl/privkey.pem
chmod 600 nginx/ssl/privkey.pem
```

### Step 3: Build & Start Services
```bash
# Build multi-stage containers and start all services in detached mode
docker compose up -d --build

# Verify all containers are running and healthy
docker compose ps
```

### Step 4: Run Database Migrations
```bash
# Execute Alembic migrations inside the API container
docker compose exec api alembic upgrade head
```

### Step 5: Verify System Health
```bash
# Probe liveness endpoint
curl -f http://localhost/health/live

# Probe readiness endpoint (verifies DB & Redis connectivity)
curl -f http://localhost/health/ready
```

Expected output:
```json
{
  "status": "ready",
  "environment": "production",
  "database": {"connected": true, "latency_ms": 2.1},
  "cache": {"connected": true, "type": "redis"}
}
```

---

## 4. Database Backup, Integrity Verification & Restore

The repository includes a dedicated operations utility: `scripts/backup_restore.py`.

### 4.1 Creating a Verified Backup
```bash
# Execute backup
python scripts/backup_restore.py --backup --dir backups/
```
The script:
1. Dumps PostgreSQL in custom compressed format (`.dump`).
2. Computes SHA-256 integrity hash.
3. Records cryptographic key fingerprints for `ENCRYPTION_KEY` and `BLIND_INDEX_KEY` in `.manifest.json`.
4. Outputs human-readable size, duration, and verification status.

### 4.2 Verifying an Existing Backup
```bash
python scripts/backup_restore.py --verify backups/krishi_mitra_backup_YYYYMMDD_HHMMSS.dump
```

### 4.3 Safe Restore Procedure
```bash
# Step 1: Verify backup file
python scripts/backup_restore.py --verify backups/krishi_mitra_backup_20261030_214732.dump

# Step 2: Execute restore with explicit confirmation flag
python scripts/backup_restore.py --restore backups/krishi_mitra_backup_20261030_214732.dump --confirm
```

---

## 5. Cryptographic Key Rotation Workflow

When rotating field-level encryption keys:
1. Keep the active `ENCRYPTION_KEY` in `.env`.
2. Move the old key to `ENCRYPTION_KEY_PREVIOUS`.
3. Generate and assign the new key to `ENCRYPTION_KEY`.
4. Restart the API service:
   ```bash
   docker compose restart api
   ```
5. `app/core/security/crypto.py` automatically attempts decryption with `ENCRYPTION_KEY`, falling back seamlessly to `ENCRYPTION_KEY_PREVIOUS` without downtime or data corruption.

---

## 6. Monitoring, Health Checks & Alerting Thresholds

| Metric | Probe Endpoint | Warning Threshold | Critical Threshold | Automated Action |
|---|---|---|---|---|
| **API Liveness** | `GET /health/live` | > 2s latency | 3 consecutive failures | Docker restarts container |
| **Database Readiness** | `GET /health/ready` | > 100ms latency | Disconnected | Alert On-Call SRE |
| **Redis Health** | `redis-cli ping` | > 20ms latency | No PONG | Fallback to in-memory store |
| **Worker Queue Backpressure** | `GET /health/ready` | Queue > 25 | Queue > 50 | 429 Too Many Requests |
| **Disk Space (Audio Buffers)** | Host filesystem | > 75% full | > 90% full | Run ephemeral cleanup job |

### Scheduled Ephemeral Audio Cleanup Job
Add to host `crontab -e`:
```bash
# Purge temporary voice recordings older than 15 minutes every 5 minutes
*/5 * * * * docker compose exec -T api python -c "from app.core.tts.storage import EphemeralAudioStore; EphemeralAudioStore().cleanup_expired()"
```

---

## 7. Rollback & Disaster Recovery Runbook

If a deployment fails verification:
1. **Immediate Rollback to Previous Container Image:**
   ```bash
   docker compose down
   git checkout <PREVIOUS_STABLE_COMMIT_HASH>
   docker compose up -d --build
   ```
2. **Revert Database Schema:**
   ```bash
   docker compose exec api alembic downgrade -1
   ```
3. **Emergency Database Restoration:**
   If data corruption occurred during a failed migration:
   ```bash
   # Re-create database and restore latest verified dump
   python scripts/backup_restore.py --restore backups/<LATEST_VALID_BACKUP>.dump --confirm
   docker compose restart api
   ```
4. **Post-Rollback Verification:**
   ```bash
   curl -f https://krishi-mitra.gov.in/health/ready
   ```
