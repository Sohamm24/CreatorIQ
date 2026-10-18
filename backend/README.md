# CreatorIQ Backend

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg?logo=redis&logoColor=white)](https://redis.io/)
[![Qdrant](https://img.shields.io/badge/Qdrant-v1.11.0-DC2626.svg?logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![LightGBM](https://img.shields.io/badge/LightGBM-4.3+-brightgreen.svg)](https://lightgbm.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)

CreatorIQ is an enterprise-grade, distributed AI microservices platform engineered for YouTube creator intelligence, real-time trend discovery, virality trajectory forecasting, and conversational growth strategy.

---

## Architecture Overview

CreatorIQ uses an asynchronous, containerized microservices architecture with a centralized API Gateway, RS256 asymmetric authentication, dedicated specialized domain services, and vector-accelerated retrieval.

```mermaid
flowchart TD
    Client["Client / Frontend (Vite / Next.js)"] -->|"HTTPS / REST / SSE"| Gateway["API Gateway (:8000)"]

    subgraph Security ["Edge Security & Verification"]
        Gateway -.->|"Verify RS256 JWT"| Secrets["RS256 Public Key"]
        Gateway -->|"Inject X-User-Id / X-Plan-Tier"| InternalNet["Internal Docker Network"]
    end

    subgraph Services ["Domain Microservices"]
        InternalNet -->|"Forward /v1/auth"| Auth["Auth Service (:8001)"]
        InternalNet -->|"Forward /v1/channels"| Channel["Channel Service (:8002)"]
        InternalNet -->|"Forward /v1/trends, /strategy, /chat"| Trend["Trend & Strategy Service (:8003)"]
        InternalNet -->|"Forward /v1/ml"| ML["ML Service (:8007)"]
    end

    subgraph DataPlane ["Persistence & Storage Layer"]
        Auth --> Postgres[("PostgreSQL 16")]
        Auth --> Redis[("Redis 7 (Session Cache)")]
        Channel --> Postgres
        Trend --> Postgres
        Trend --> Redis
        Trend --> Qdrant[("Qdrant Vector DB (:6333)")]
        ML --> Postgres
    end

    subgraph ExternalPipelines ["External Ingestion & Inference"]
        Trend --> YouTube["YouTube Data API v3 Pool"]
        Trend --> SerpApi["SerpApi / Google Trends"]
        Trend --> Tavily["Tavily Search API"]
        Trend --> LLM["Groq / Gemini / OpenAI / OpenRouter"]
    end
```

---

## Active Services

### 1. API Gateway (`:8000`)
- **Reverse Proxy & Routing**: Acts as the single entry point (`/v1/*`), forwarding requests to target internal microservices based on route prefixes.
- **Asymmetric JWT Verification**: Validates incoming Bearer tokens using RS256 public key cryptography (`jwt_public.pem`). Upon verification, it strips spoofable headers and injects trusted internal headers (`X-User-Id`, `X-Plan-Tier`, `X-Request-Id`).
- **Streaming Response Gateway**: Native support for Server-Sent Events (SSE) streaming (`/v1/strategy/chat/stream`) with HTTPX async chunk forwarding.
- **Route Whitelisting**: Allows unauthenticated access to public routes (`auth/login`, `auth/register`, `auth/token/refresh`, `ml/evaluations/*`, and health probes).

### 2. Auth Service (`:8001`)
- **Identity & Access Management**: User registration, login, profile retrieval, and onboarding completion.
- **Security Primitives**: Password hashing via BCrypt, short-lived RS256 access tokens, and refresh tokens stored using SHA-256 peppered hashing.
- **Multi-Device Session Tracking**: Tracks active user sessions with IP address, user-agent metadata, and automatic expiration.

### 3. Channel Service (`:8002`)
- **Creator Profile & Niche Management**: Manages creator identity, selected/inferred niches, tone of voice, content format preferences (Shorts, Long-form, Both), and publishing frequency.
- **Channel Analytics**: Tracks historical views, subscriber growth, engagement rates, and metrics refreshes.
- **Adaptive Profiling**: Supports manual creator onboarding and analysis-assisted profile reconfiguration.
- **Context Provider**: Serves internal channel context payloads to downstream services for personalized AI strategy generation.

### 4. Trend & Strategy Service (`:8003`)
- **Multi-Source Trend Harvester**:
  - **YouTube Data API v3 Pool**: Multi-key rotating collector pool with daily quota tracking (`api_request_logs`) to maximize ingestion within rate limits.
  - **Discovery Harvester**: Integrates Google Trends, SerpApi, Tavily, and trending video scrapers.
  - **LLM Concept Deduplication**: Uses high-speed LLMs (Groq, Gemini, OpenRouter) to clean raw search queries into canonical concepts.
- **TVS (Trend Virality Score) Engine**:
  - Calculates reach ratios, interaction densities, outlier streaks across channel tiers (small, medium, large channels), and lifecycle transitions (`emerging`, `growing`, `peaking`, `declining`).
- **AI Strategy & Conversational Copilot**:
  - Multi-turn strategy chat sessions (`/v1/strategy/sessions`, `/v1/strategy/chat`).
  - Low-latency SSE streaming (`/v1/strategy/chat/stream`).
  - Qdrant Vector Search integration (`:6333`) for semantic creator memory embeddings and personalized recommendation feeds.

### 5. ML Service (`:8007`)
- **85-Feature LightGBM Virality Forecasting**:
  - Trajectory and probability forecasting model using 9 base metrics, 5 lag horizons (1, 3, 7, 14, 28 days), 4 rolling windows, and 8 momentum indicators.
  - Predicts 90-day virality curves, confidence intervals, and estimated lifecycle peaks.
- **Automated Model Telemetry & Evaluation**:
  - Logs MAE, RMSE, MAPE, R2 score, latency, and sample size for every forecast run.
  - Writes dual-tier telemetry: local rotating JSONL evaluation logs and persistent `ml_model_evaluations` database records.
  - Exposes public observability endpoints for accuracy auditing without credentials.

---

## Key API Endpoints

All external API calls must target the **API Gateway** on port `8000` under the `/v1` prefix.

### Authentication (`/v1/auth`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/v1/auth/register` | Register a new user | No |
| `POST` | `/v1/auth/login` | Authenticate user & issue RS256 token pair | No |
| `POST` | `/v1/auth/token/refresh` | Rotate and issue a new access token | No |
| `GET` | `/v1/auth/me` | Fetch currently authenticated user profile | Yes (Bearer) |
| `PATCH` | `/v1/auth/onboarding/complete`| Finalize onboarding preferences | Yes (Bearer) |
| `GET` | `/v1/auth/health` | Health status of the Auth Service | No |

### Channels & Profiles (`/v1/channels`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/v1/channels/me` | Retrieve creator channel details | Yes (Bearer) |
| `GET` | `/v1/channels/profile` | Fetch creator profile and niche settings | Yes (Bearer) |
| `PUT` | `/v1/channels/profile` | Update creator profile settings | Yes (Bearer) |
| `POST` | `/v1/channels/profile/reconfigure` | Reconfigure creator profile & target audience | Yes (Bearer) |
| `GET` | `/v1/channels/{channel_id}/metrics` | Fetch channel performance metrics | Yes (Bearer) |

### Trends & Discovery (`/v1/trends`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/v1/trends` | Paginated personalized trend feed | Yes (Bearer) |
| `POST` | `/v1/trends/refresh` | Force refresh trend feed | Yes (Bearer) |
| `GET` | `/v1/trends/{trend_id}` | Trend details, lifecycle, and signals | Yes (Bearer) |
| `GET` | `/v1/trends/{trend_id}/forecast` | Retrieve ML 90-day trajectory forecast | Yes (Bearer) |
| `GET` | `/v1/trends/saved` | List creator saved trends | Yes (Bearer) |
| `POST` | `/v1/trends/{trend_id}/save` | Bookmark a trend | Yes (Bearer) |
| `DELETE` | `/v1/trends/{trend_id}/save` | Remove trend bookmark | Yes (Bearer) |

### AI Strategy & Copilot (`/v1/strategy`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/v1/strategy/sessions` | List creator strategy chat sessions | Yes (Bearer) |
| `POST` | `/v1/strategy/sessions` | Create a new strategy session | Yes (Bearer) |
| `GET` | `/v1/strategy/sessions/{id}` | Retrieve chat message history | Yes (Bearer) |
| `DELETE` | `/v1/strategy/sessions/{id}` | Delete a chat session | Yes (Bearer) |
| `POST` | `/v1/strategy/chat` | Synchronous AI strategy recommendation | Yes (Bearer) |
| `POST` | `/v1/strategy/chat/stream` | **Real-time SSE streaming** AI response | Yes (Bearer) |
| `GET` | `/v1/strategy/memory` | Retrieve vector memory associations | Yes (Bearer) |

### Machine Learning Observability (`/v1/ml`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/v1/ml/evaluations/summary` | Aggregated accuracy, MAE, RMSE, and latency | No |
| `GET` | `/v1/ml/evaluations/recent` | Recent evaluation audit records | No |
| `GET` | `/v1/ml/health` | Health status of ML forecast engine | No |

---

## Database Architecture

The system utilizes PostgreSQL 16 with domain-isolated tables and asynchronous connection pooling via `asyncpg`.

- **`users` & `sessions`**: User credentials, role tiers, hashed refresh tokens, and session metadata.
- **`creator_profiles` & `channels`**: Niches (onboarding, inferred, and effective), tone preferences, target audience geo-weights, and subscriber/view metrics.
- **`trend_concepts` & `concept_daily_signals`**: Canonical topics, reach ratios, interaction densities, outlier videos, and lifecycle statuses.
- **`trend_feed_snapshots`**: Cached feed results generated for individual users based on niche affinity.
- **`chat_sessions` & `chat_messages`**: Persistent conversational strategy history.
- **`ml_model_evaluations`**: Live validation metrics (MAE, RMSE, R2, CI coverage) from ML inference.
- **`api_request_logs`**: External API quota accounting and latency diagnostics.

---

## Quick Start & Local Development

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- [Python 3.11+](https://www.python.org/downloads/) (for running local scripts or Conda environments).
- PowerShell (on Windows) or Bash (on Linux/macOS).
- OpenSSL (optional, Python `cryptography` fallback is included).

### 1. Clone & Configure Environment
Navigate to the `backend/` directory:
```bash
cd backend
cp .env.example .env
```
Populate `.env` with your API keys (see [Environment Configuration](#environment-configuration)).

### 2. Generate RS256 JWT Keypair
Run the automated key generation script to create `jwt_private.pem` and `jwt_public.pem` in `backend/secrets/`:

```powershell
# Windows PowerShell
.\scripts\generate-jwt-keys.ps1
```
*On Linux/macOS:*
```bash
mkdir -p secrets
openssl genrsa -out secrets/jwt_private.pem 2048
openssl rsa -in secrets/jwt_private.pem -pubout -out secrets/jwt_public.pem
```

### 3. Start Stack with Docker
Launch the entire backend stack (infrastructure, schema push, and microservices) with one command:

```powershell
# Windows PowerShell
.\scripts\docker-up.ps1
```

*Or manually via Docker Compose:*
```bash
# 1. Build images
docker compose build
docker compose --profile db-push build

# 2. Start PostgreSQL, Redis, and Qdrant
docker compose up -d postgres redis qdrant

# 3. Synchronize database schemas
docker compose --profile db-push run --rm db-push-auth
docker compose --profile db-push run --rm db-push-channel
docker compose --profile db-push run --rm db-push-trend

# 4. Start all microservices
docker compose up -d
```

### 4. Verify System Health
Once started, test the API Gateway and underlying services:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/v1/auth/health
curl http://localhost:8000/v1/ml/health
```

---

## Environment Configuration

Configure the following variables in `backend/.env`:

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Deployment environment (`development` or `production`) | `development` |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://creatoriq:creatoriq@postgres:5432/creatoriq` |
| `REDIS_URL` | Redis instance URL | `redis://redis:6379/0` |
| `QDRANT_URL` | Qdrant vector database URL | `http://qdrant:6333` |
| `JWT_ISSUER` | JWT token issuer | `creatoriq-auth` |
| `JWT_AUDIENCE` | JWT token audience | `creatoriq-api` |
| `JWT_PUBLIC_KEY_PATH` | Path to RS256 public key | `/run/secrets/jwt_public.pem` |
| `JWT_PRIVATE_KEY_PATH`| Path to RS256 private key | `/run/secrets/jwt_private.pem` |
| `INTERNAL_SERVICE_TOKEN`| Shared token for secure inter-service communication | `your-secure-internal-token` |
| `FRONTEND_URL` | Allowed CORS origins (comma-separated) | `http://localhost:5173` |
| `YOUTUBE_API_KEY` | Primary YouTube Data API v3 key | `AIzaSy...` |
| `YOUTUBE_API_KEY_2` | Secondary key for rotation pool | `AIzaSy...` |
| `YOUTUBE_API_KEY_3` | Tertiary key for rotation pool | `AIzaSy...` |
| `SERPAPI_API_KEY` | SerpApi key for Google Trends discovery | `your-serpapi-key` |
| `TAVILY_API_KEYS` | Tavily API key for real-time web topic harvesting | `tvly-...` |
| `GROQ_API_KEYS` | Groq API key(s) for fast LLM inference | `gsk_...` |
| `GEMINI_API_KEYS` | Google Gemini API key(s) | `AIzaSy...` |
| `OPENROUTER_API_KEY` | OpenRouter API key | `sk-or-...` |
| `MODEL_NAME` | Default LLM model identifier | `openai/gpt-4o-mini` |

---

## Production Deployment

A dedicated production compose configuration is provided in [`docker-compose.prod.yml`](file:///c:/Users/Soham/Desktop/Projects/CreatorIQ/CreatorIQ/backend/docker-compose.prod.yml):
- Pre-built image pulling from GHCR (`ghcr.io/yashparmar1125/creatoriq-*`).
- Memory limits on compute-heavy services (e.g. 1.2GB cap on ML, 800MB on Trend).
- JSON-file log rotation policies.
- Internal gateway port binding (`127.0.0.1:8000`) for upstream reverse proxies like Caddy or Nginx.

To trigger an automated server deploy, execute [`scripts/deploy.sh`](file:///c:/Users/Soham/Desktop/Projects/CreatorIQ/CreatorIQ/backend/scripts/deploy.sh):
```bash
./scripts/deploy.sh
```

---

## Project Structure

```
backend/
├── docker-compose.yml          # Local multi-container Docker specification
├── docker-compose.prod.yml     # Hardened production Docker specification
├── .env.example                # Template for environment configuration
├── scripts/
│   ├── docker-up.ps1           # Windows one-click stack launcher & validator
│   ├── generate-jwt-keys.ps1   # RS256 RSA keypair generator
│   ├── deploy.sh               # Automated production server deployment script
│   ├── purge_and_hydrate_real_youtube.py # YouTube Data API hydration utility
│   └── schema.sql              # Master PostgreSQL reference schema
└── services/
    ├── api-gateway/            # Gateway: Auth validation, routing & SSE proxy
    ├── auth/                   # Identity: Users, sessions, and JWT tokens
    ├── channel/                # Channel metadata, creator profiles, metrics
    ├── trend/                  # Discovery, TVS scoring, Qdrant & AI Strategy
    └── ml/                     # LightGBM 85-feature forecasting & telemetry
```
