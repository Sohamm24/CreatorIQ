# CreatorIQ — AI-Powered Trend Intelligence & Strategy Platform for YouTube Creators

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-6+-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.0-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg?logo=redis&logoColor=white)](https://redis.io/)
[![Qdrant](https://img.shields.io/badge/Qdrant-v1.11.0-DC2626.svg?logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![LightGBM](https://img.shields.io/badge/LightGBM-4.3+-brightgreen.svg)](https://lightgbm.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)

**CreatorIQ** is a distributed, AI-driven creator intelligence platform that detects emerging YouTube trends, calculates niche-calibrated virality scores, forecasts 90-day trajectory curves, and generates AI content strategies.

[Features](#-key-features) • [Architecture](#-system-architecture) • [Active Microservices](#-active-microservices) • [Tech Stack](#-tech-stack) • [Quickstart](#-getting-started) • [API Reference](#-api-reference)

</div>

---

## 💡 What is CreatorIQ?

Modern creators struggle with content decision-making: picking saturated topics, chasing fleeting spikes too late, or adopting trends misaligned with their audience. **CreatorIQ** solves this with a high-throughput, data-driven workflow:

1. **Automated Multi-Source Harvesting**: Continuously captures raw video and search velocity signals from YouTube Data API v3 and Google Trends (SerpApi).
2. **Quality Gating & English Filtering**: Filters noise, spam, and non-English keywords before database persistence.
3. **Semantic Vector Personalization**: Maps creator niche profiles to trend concepts using 384-dimensional dense vectors (`all-MiniLM-L6-v2`) in Qdrant Vector DB.
4. **Statistical Breakout Detection**: Identifies viral breakouts using moving average and standard deviation anomaly gates ($\mu + 2\sigma$).
5. **85-Feature Machine Learning Forecasting**: Projects 90-day virality trajectories, confidence intervals, and lifecycle peak dates using LightGBM.
6. **Conversational Strategy Copilot**: Generates personalized video hooks, outlines, titles, and SEO tags via real-time Server-Sent Events (SSE) streaming.

---

## 🏛️ System Architecture

CreatorIQ is built as an asynchronous microservice mesh coordinated through a centralized API Gateway with RS256 asymmetric JWT verification, dedicated domain microservices, and dedicated persistence layers.

```mermaid
flowchart TD
    Client["Client / Frontend (React 19 + Vite) :5173"] -->|"REST / HTTPS / SSE"| Gateway["API Gateway (FastAPI) :8000"]

    subgraph Security ["Edge Security & Verification"]
        Gateway -.->|"Verify RS256 JWT"| Secrets["jwt_public.pem"]
        Gateway -->|"Inject X-User-Id / X-Plan-Tier"| InternalNet["Docker Virtual Network (creatoriq-net)"]
    end

    subgraph Microservices ["Core Domain Microservices"]
        InternalNet -->|"Proxy /v1/auth"| Auth["Auth Service :8001"]
        InternalNet -->|"Proxy /v1/channels"| Channel["Channel Service :8002"]
        InternalNet -->|"Proxy /v1/trends, /strategy, /chat"| Trend["Trend & Strategy Service :8003"]
        InternalNet -->|"Proxy /v1/ml"| ML["ML Service :8007"]
    end

    subgraph Datastores ["Persistence & Vector Search"]
        Auth --> Postgres[("PostgreSQL 16")]
        Auth --> Redis[("Redis 7 (Session Cache)")]
        Channel --> Postgres
        Trend --> Postgres
        Trend --> Redis
        Trend --> Qdrant[("Qdrant Vector DB :6333")]
        ML --> Postgres
    end

    subgraph Pipelines ["External Ingestion & Model Inference"]
        Trend --> YouTube["YouTube Data API v3 Pool"]
        Trend --> SerpApi["SerpApi / Google Trends"]
        Trend --> LLM["Groq / Gemini / OpenAI / OpenRouter"]
        Trend <--> ML
    end
```

---

## 🚀 Active Microservices

| Service | Port | Directory | Core Responsibilities |
| :--- | :---: | :--- | :--- |
| **API Gateway** | `8000` | [`backend/services/api-gateway`](file:///backend/services/api-gateway) | Single public entry point (`/v1/*`), RS256 JWT validation, header sanitization (`X-User-Id`, `X-Plan-Tier`), SSE streaming proxy, public route whitelisting. |
| **Auth Service** | `8001` | [`backend/services/auth`](file:///backend/services/auth) | User registration, login, BCrypt password hashing, session metadata tracking, RS256 token issuance & SHA-256 refresh token rotation. |
| **Channel Service** | `8002` | [`backend/services/channel`](file:///backend/services/channel) | Creator channel identity, manual onboarding profile, target audience geography, niche preferences, content format (Shorts/Long-form), tone of voice. |
| **Trend & Strategy** | `8003` | [`backend/services/trend`](file:///backend/services/trend) | Multi-source ingest (YouTube + SerpApi), `langdetect` quality gate, 384-dim Qdrant vector indexing, TVS scoring, outlier breakout detection ($\mu + 2\sigma$), AI Strategy Copilot with SSE streaming. |
| **ML Service** | `8007` | [`backend/services/ml`](file:///backend/services/ml) | 85-feature LightGBM virality forecast engine, 90-day trajectory curves, Bayesian confidence intervals, automated evaluation telemetry (MAE, RMSE, MAPE, R²). |
| **Frontend Web** | `5173` | [`frontend`](file:///frontend) | React 19, TypeScript, Tailwind CSS 4, Zustand, Vite. Interactive onboarding wizard, personalized trend discovery feed, ML forecast charts, strategy chat, public audit page. |

---

## ✨ Key Features

### 1. Personalized Trend Intelligence Feed
- **Niche-Specific Scoring**: Ranks concepts according to creator niches, audience geography, and preferred content format.
- **Statistical Outlier Detection**: Flags topics whose raw momentum exceeds the pool baseline by $\mu + 2\sigma$, granting a scoring bonus for rapid breakouts.
- **Creator Tier Classification**: Categorizes trends into `small`, `medium`, and `big` channel buckets using search volume quartiles ($Q_{25}$ and $Q_{75}$).
- **Soft Diversity Balancing**: Prevents mega-channel dominance by ensuring smaller creators are surfaced in high-ranking slots.

### 2. Semantic Search & Vector Memory (Qdrant)
- **Model**: `sentence-transformers/all-MiniLM-L6-v2` generating 384-dimensional dense embeddings.
- **Deterministic Embeddings**: Eliminates hash-randomization defects with deterministic neural representations.
- **Write-Path Asynchronous Indexing**: Vector generation runs on background collector jobs, keeping the read feed API fast and non-blocking.
- **Self-Healing Collections**: Auto-detects and migrates outdated vector dimensions on startup.

### 3. 85-Feature LightGBM Virality Forecasting
- **Multi-Horizon Feature Pipeline**:
  - **9 Base Metrics**: Trend score, population size, reach ratios, interaction density, semantic scores, outlier streak, and creator tier counts.
  - **25 Lag Features**: 5 metrics across 5 historical lag horizons (1, 3, 7, 14, 28 days).
  - **20 Rolling Features**: Moving window averages across 3, 7, 14, and 28 days.
  - **8 Momentum Indicators**: Multi-day acceleration differentials and momentum streaks.
- **90-Day Trajectory Curve**: Predicts lifecycle transitions (`emerging` → `growing` → `peaking` → `declining`).
- **Public Model Observability**: Live evaluation metrics (MAE, RMSE, MAPE, R², latency) accessible via public audit endpoints.

### 4. AI Strategy Copilot & Content Briefs
- **Multi-Turn Chat**: Context-aware content ideation grounded in the creator's channel profile and active trend signals.
- **Real-Time Streaming**: Native Server-Sent Events (SSE) streaming via `/v1/strategy/chat/stream`.
- **Structured Brief Generation**: Automatically creates titles, hooks, video script outlines, and SEO keyword tags.

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS 4, Zustand, Lucide React, Framer Motion, Axios |
| **API & Backend** | FastAPI, Python 3.11+, Pydantic v2, SQLAlchemy (Asyncio), Asyncpg, HTTPX, APScheduler |
| **Machine Learning** | LightGBM, Scikit-Learn, Pandas, NumPy, Sentence-Transformers (`all-MiniLM-L6-v2`) |
| **Databases & Cache** | PostgreSQL 16, Redis 7, Qdrant Vector DB (v1.11.0) |
| **Security & Auth** | Asymmetric RS256 JWT, Cryptography (PEM keys), BCrypt, Zero-Trust Gateway header injection |
| **Data Ingestion** | YouTube Data API v3 (multi-key pool), SerpApi (Google Trends), `langdetect` |
| **DevOps & Containers** | Docker, Docker Compose, Ansible, Caddy / Nginx reverse proxy |

</div>

---

## 📂 Repository Structure

```
CreatorIQ/
├── backend/
│   ├── docker-compose.yml           # Local development multi-container topology
│   ├── docker-compose.prod.yml      # Production container specification
│   ├── scripts/
│   │   ├── docker-up.ps1            # Automated Windows/PowerShell startup orchestrator
│   │   ├── generate-jwt-keys.ps1    # RS256 RSA key pair generator
│   │   ├── schema.sql               # Unified PostgreSQL database schema
│   │   └── deploy.sh                # Production Linux deployment runner
│   └── services/
│       ├── api-gateway/             # Central reverse proxy (:8000) & JWT security gate
│       ├── auth/                    # User identity, sessions, and RS256 token service (:8001)
│       ├── channel/                 # Creator profile, niches, format, and audience context (:8002)
│       ├── ml/                      # 85-feature LightGBM forecasting & telemetry (:8007)
│       └── trend/                   # Trend harvester, Qdrant vectors, TVS ranking, AI strategy (:8003)
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  # React Router 7 route definitions
│   │   ├── components/              # Shared UI primitives, cards, badges, and layout
│   │   ├── features/
│   │   │   ├── dashboard/           # Channel overview and key stats
│   │   │   ├── onboarding/          # 5-step manual creator onboarding wizard
│   │   │   ├── settings/            # Channel profile configuration and preferences
│   │   │   ├── strategy/            # AI Strategy Copilot and content brief generator
│   │   │   └── trends/              # Trends feed, filter controls, and trend detail page
│   │   ├── pages/                   # Landing, Product, Pricing, Insights, Model Performance
│   │   └── stores/                  # Zustand state stores (auth, trends, strategy)
│   ├── package.json
│   └── vite.config.ts
├── infra/
│   └── ansible/                     # Deployment playbooks & server configuration
└── docs/                            # Deep-dive architecture and technical specs
```

---

## ⚡ Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Compose v2 enabled)
- [Node.js](https://nodejs.org/) (v18+ or v20+) and `npm`
- [Python](https://www.python.org/) 3.11+ (optional, if running services outside Docker)
- OpenSSL or PowerShell (for generating RS256 key pairs)

---

### 1. Environment Configuration

#### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Copy the sample environment file:
   ```bash
   cp .env.example .env
   # On Windows PowerShell:
   Copy-Item .env.example .env
   ```
3. Configure the essential keys in `backend/.env`:
   ```env
   ENVIRONMENT=development
   LOG_LEVEL=INFO

   # Database & Cache (Docker defaults)
   DATABASE_URL=postgresql+asyncpg://creatoriq:creatoriq@postgres:5432/creatoriq
   REDIS_URL=redis://redis:6379/0
   QDRANT_URL=http://qdrant:6333

   # Security & Cryptography
   JWT_ISSUER=creatoriq-auth
   JWT_AUDIENCE=creatoriq-api
   JWT_PUBLIC_KEY_PATH=/run/secrets/jwt_public.pem
   JWT_PRIVATE_KEY_PATH=/run/secrets/jwt_private.pem
   INTERNAL_SERVICE_TOKEN=local-dev-internal-token
   AES_ENCRYPTION_KEY=WDKoTVeDqkigRBrzrrJ-pZ4j6qcUguac_zFtDHJgqKE=

   # External Signal APIs (Required for live trend collection)
   YOUTUBE_API_KEY=your_youtube_data_api_v3_key
   SERPAPI_API_KEY=your_serpapi_key
   OPENROUTER_API_KEY=your_llm_api_key
   MODEL_NAME=openai/gpt-4o-mini
   ```

#### RSA Key Pair Generation

CreatorIQ requires an RSA-256 key pair for cryptographic token signing.

- **PowerShell (Windows)**:
  ```powershell
  .\scripts\generate-jwt-keys.ps1
  ```
- **Bash / Linux / macOS**:
  ```bash
  mkdir -p secrets
  openssl genrsa -out secrets/jwt_private.pem 2048
  openssl rsa -in secrets/jwt_private.pem -pubout -out secrets/jwt_public.pem
  chmod 600 secrets/jwt_private.pem
  ```

---

### 2. Running with Docker Compose (Recommended)

From the project root:

```bash
# Automated boot script (PowerShell)
.\backend\scripts\docker-up.ps1
```

Or using standard Docker CLI:

```bash
cd backend

# 1. Start core data stores
docker compose up -d postgres redis qdrant

# 2. Sync database schemas via one-shot sync runners
docker compose --profile db-push run --rm db-push-auth
docker compose --profile db-push run --rm db-push-channel
docker compose --profile db-push run --rm db-push-trend

# 3. Start all microservices and API Gateway
docker compose up -d
```

#### Verify Backend Service Health

```bash
curl http://localhost:8000/health
```

Expected output:
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "version": "v1",
  "environment": "development"
}
```

---

### 3. Running the Frontend

In a separate terminal:

```bash
cd frontend

# Install dependencies
npm install

# Create environment configuration
echo "VITE_API_URL=http://localhost:8000/v1" > .env

# Start development server
npm run dev
```

Visit **http://localhost:5173** in your browser.

---

## 🧪 End-to-End User Walkthrough

1. **Sign Up**: Navigate to `http://localhost:5173/signup` and create an account.
2. **Interactive Onboarding (5 Steps)**:
   - **Step 1**: Welcome & platform overview.
   - **Step 2**: Enter channel name, handle, and subscriber range.
   - **Step 3**: Select 1–3 target creator niches (e.g., Tech, AI, Gaming).
   - **Step 4**: Choose preferred format (`Long-form`, `Shorts`, `Both`), publishing frequency, and target audience country.
   - **Step 5**: Review calibrated profile and finalize onboarding.
3. **Explore Trends**:
   - Access the personalized Top 15 opportunities at `/app/trends`.
   - Inspect outlier badges, tier tags, and search volume indicators.
4. **Inspect Forecasts**:
   - Open a trend detail page (`/app/trends/detail/:id`).
   - Examine the LightGBM 90-day trajectory curve and estimated view potential.
5. **Generate Strategy**:
   - Click "Generate Strategy" on any trend to launch the AI Strategy Copilot (`/app/strategy`).
   - Stream video hooks, outlines, and content angles in real time.

---

## 📡 API Reference

All client interactions pass through the **API Gateway** on port `8000` with the `/v1` prefix.

### Authentication (`/v1/auth`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/v1/auth/register` | Register new creator account | No |
| `POST` | `/v1/auth/login` | Authenticate user & issue RS256 token pair | No |
| `POST` | `/v1/auth/token/refresh` | Rotate and refresh access token | No |
| `GET` | `/v1/auth/me` | Retrieve profile of authenticated user | Yes |
| `PATCH` | `/v1/auth/onboarding/complete`| Save onboarding preferences | Yes |
| `GET` | `/v1/auth/health` | Health probe for Auth Service | No |

### Channels & Creator Profiles (`/v1/channels`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/v1/channels/me` | Retrieve current creator's channel | Yes |
| `GET` | `/v1/channels/profile` | Fetch creator profile and niche calibration | Yes |
| `PUT` | `/v1/channels/profile` | Update profile settings | Yes |
| `POST` | `/v1/channels/profile/reconfigure` | Reconfigure niches and target audience | Yes |
| `GET` | `/v1/channels/{channel_id}/metrics` | Fetch channel analytics & metrics | Yes |

### Trend Discovery & Ingestion (`/v1/trends`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/v1/trends` | Paginated personalized trend feed | Yes |
| `POST` | `/v1/trends/refresh` | Force recalculate trend feed | Yes |
| `GET` | `/v1/trends/{trend_id}` | Trend concept details, volume & lifecycle | Yes |
| `GET` | `/v1/trends/{trend_id}/forecast` | 90-day ML trajectory & virality forecast | Yes |
| `GET` | `/v1/trends/saved` | List saved / bookmarked trends | Yes |
| `POST` | `/v1/trends/{trend_id}/save` | Save a trend concept | Yes |
| `DELETE`| `/v1/trends/{trend_id}/save` | Remove a saved trend | Yes |

### AI Strategy & Copilot (`/v1/strategy`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/v1/strategy/sessions` | List creator chat sessions | Yes |
| `POST` | `/v1/strategy/sessions` | Initialize a new strategy chat session | Yes |
| `GET` | `/v1/strategy/sessions/{id}` | Fetch session chat message history | Yes |
| `DELETE`| `/v1/strategy/sessions/{id}` | Delete a chat session | Yes |
| `POST` | `/v1/strategy/chat` | Synchronous AI recommendation | Yes |
| `POST` | `/v1/strategy/chat/stream` | **SSE Real-Time Streaming** response | Yes |
| `GET` | `/v1/strategy/memory` | Retrieve vector memory associations | Yes |

### Machine Learning Observability (`/v1/ml`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/v1/ml/evaluations/summary` | Aggregated model metrics (MAE, RMSE, MAPE, R²) | No |
| `GET` | `/v1/ml/evaluations/recent` | Recent forecast audit telemetry | No |
| `GET` | `/v1/ml/health` | Health probe for ML forecast engine | No |

---

## 🔒 Security Architecture

- **Zero-Trust Internal Network**: Microservices operate on an isolated Docker bridge network (`creatoriq-net`). Only the API Gateway exposes port `8000` to the host/reverse-proxy.
- **Asymmetric RS256 Tokens**: Access tokens are signed using an RSA private key (`jwt_private.pem`) held strictly by `ciq-auth`. Downstream services verify tokens via the public key (`jwt_public.pem`).
- **Header Injection Guard**: The API Gateway explicitly strips spoofable user headers (`X-User-Id`, `X-Plan-Tier`) from incoming client requests and injects verified values only after cryptographic token validation.
- **Internal Service Authentication**: Inter-service endpoints (`/internal/*`) require an `X-Internal-Service-Token` header for protected service-to-service communication.

---

## 🚢 Production Deployment

CreatorIQ is production-ready for deployment on cloud virtual machines (Ubuntu / Azure / AWS / GCP) using Docker Compose:

1. **Deploy Script**: Use the automated PowerShell deployment script [`deploy.ps1`](file:///deploy.ps1):
   ```powershell
   .\deploy.ps1 -VmHost "your-server-ip" -VmUser "ubuntu" -IdentityFile "~/.ssh/id_rsa"
   ```
2. **Production Compose**: [`backend/docker-compose.prod.yml`](file:///backend/docker-compose.prod.yml) binds the API Gateway to `127.0.0.1:8000` to sit securely behind a reverse proxy (e.g., Caddy with automated Let's Encrypt SSL).
3. **Container Resource Limits**: Dedicated memory envelopes configured for memory-intensive services (ML service limited to 1200MB, Trend service limited to 800MB).

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
