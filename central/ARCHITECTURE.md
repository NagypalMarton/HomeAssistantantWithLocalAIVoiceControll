# Central Backend - Architektúra Döntések & Konfiguráció

**Verzió:** 1.0  
**Dátum:** 2026. január 23.  
**Status:** Implementálva (User API + HA Manager alapstruktúra)

## 📋 Hozott Döntések

### 1. **Deployment & Orchestration**
| Döntés | Indoklás |
|--------|----------|
| **Docker Compose (dev/staging)** | Gyors fejlesztés, könnyű setup |
| **Kubernetes (prod, később)** | Skalázhatóság, enterprise support |
| **GPU Docker support** | Ollama Ministral-3 GPU acceleration |

### 2. **Home Assistant Management**
| Döntés | Indoklás |
|--------|----------|
| **Per-user Docker containers** | Teljes izoláltsága, biztonsági szegmentáció |
| **Egy user = egy HA instance** | Adatvédelem, felhasználói autonómia |
| **Port range: 8200-8300** | 100 egyidejű user támogatása |
| **Volume per instance** | Persistent storage, easy cleanup |

### 3. **LLM Konfiguráció**
| Döntés | Indoklás |
|--------|----------|
| **Modell: Ministral-3 3B Instruct Q4_K_M** | 3B params, 4GB vRAM, magyar támogatás |
| **GPU acceleration (NVIDIA)** | Gyorsabb inference (~100ms vs 1s CPU) |
| **Prompt engineering** | JSON output intent parsing |
| **Timeout: 30s** | Balance latency vs accuracy |

### 4. **Biztonsági Szint**
| Döntés | Indoklás |
|--------|----------|
| **JWT autentikáció** | Stateless, scalable |
| **Token encryption (Fernet)** | HA API token-ok protected |
| **Per-user Docker isolation** | Network policies |
| **Audit logging** | Compliance & debugging |
| **SQL parameterization** | SQL injection protection |

### 5. **Monitoring & Logging**
| Döntés | Indoklás |
|--------|----------|
| **Structlog (JSON)** | Searchable, centralized logging |
| **Prometheus (opcionális)** | Metrics collection |
| **Zabbix (külön Compose)** | Production-grade monitoring |

## 🏗️ Aktuális Implementáció

### Service Topológia

```
┌─────────────────────────────────────────────────────────┐
│ Docker Compose (central)                                 │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐   │
│  │  postgres   │  │    redis    │  │    ollama    │   │
│  │  port 5432  │  │  port 6379  │  │  port 11434  │   │
│  │ central_db  │  │ cache/queue │  │ (GPU) LLM    │   │
│  └─────────────┘  └─────────────┘  └──────────────┘   │
│        ↑                ↑                ↑              │
│        └────────────────┴────────────────┘              │
│                         │                               │
│  ┌──────────────────────┴──────────────────────┐       │
│  │                                              │       │
│  │  ┌──────────────────┐  ┌────────────────┐  │       │
│  │  │   user-api       │  │  ha-manager    │  │       │
│  │  │   port 8000      │  │  port 8001     │  │       │
│  │  │ Intent processing│  │ Docker mgmt    │  │       │
│  │  └──────────────────┘  └────────────────┘  │       │
│  │          ↑                     ↑            │       │
│  │          └─────────────────────┘            │       │
│  │          (internal HTTP)                    │       │
│  │                                              │       │
│  └──────────────────────────────────────────────┘     │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Docker-in-Docker: Per-user HA instances         │   │
│  │ (8200-8300 port range)                          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘

Edge (Pi) ──Wyoming──→ User API (8000) ──Intent──→ LLM (11434)
                                ↓
                          HA Manager (8001)
                                ↓
                        User HA Instance (8200+)
```

### Database Schema

```sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  password_hash VARCHAR NOT NULL,
  ha_instance_url VARCHAR,           -- Per-user HA instance URL
  ha_token_encrypted TEXT,            -- Encrypted HA token (Fernet)
  role VARCHAR DEFAULT 'user',
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Sessions table (context window)
CREATE TABLE sessions (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  device_id VARCHAR,                  -- Edge device ID
  created_at TIMESTAMP,
  expires_at TIMESTAMP,
  context JSON                        -- Rolling message history
);

-- HA Instances table
CREATE TABLE ha_instances (
  id UUID PRIMARY KEY,
  user_id UUID UNIQUE NOT NULL,       -- One instance per user
  container_id VARCHAR,               -- Docker container ID
  container_name VARCHAR UNIQUE,
  status VARCHAR,                     -- started/stopped/error
  host_port INT UNIQUE,               -- 8200-8300
  docker_network VARCHAR,
  timezone VARCHAR,
  internal_api_token VARCHAR,
  config_yaml TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Audit log table
CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP,
  user_id UUID,
  device_id VARCHAR,
  input_text TEXT,                   -- Original user text
  intent JSON,                        -- Parsed intent
  ha_response JSON,                   -- HA execution result
  status VARCHAR,                     -- success/error
  latency_ms INT,
  llm_tokens INT,
  error_message TEXT,
  request_id VARCHAR UNIQUE
);
```

### Port Mapping

| Service | Port | Hozzáférés |
|---------|------|-----------|
| User API | 8000 | localhost:8000 |
| HA Manager | 8001 | localhost:8001 (internal) |
| Ollama | 11434 | localhost:11434 (internal) |
| PostgreSQL | 5432 | localhost:5432 (internal) |
| Redis | 6379 | localhost:6379 (internal) |
| Prometheus | 9090 | localhost:9090 (optional) |
| **User HA instances** | 8200-8300 | localhost:8200+ |

### Environment Variables

```bash
# Kritikus (prod-ben kötelező)
JWT_SECRET=<python -c 'import secrets; print(secrets.token_urlsafe(32))'>
ENCRYPTION_KEY=<python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'>
DATABASE_URL=postgresql://...
DOCKER_HOST=unix:///var/run/docker.sock

# Ollama
OLLAMA_MODEL=ministral-3:3b-instruct-2512-q4_K_M
LLM_TIMEOUT_SECONDS=30

# HA Manager
HA_PORT_RANGE_START=8200
HA_PORT_RANGE_END=8300
HA_MEMORY_LIMIT=512m
HA_CPU_LIMIT=0.5
```

## 📊 Intent Processing Flow

```
1. Edge eszköz → User API (/api/v1/intent)
   {
     user_id: uuid,
     device_id: "pi-1",
     text: "Kapcsold be a nappali lámpát"
   }

2. User API:
   - JWT token validálás
   - Session context betöltés (Redis)
   
3. LLM Service (Ollama):
   - Prompt building (context + user text)
   - Ministral-3 inference
   - Intent parsing (JSON)
   
   Response:
   {
     "intent": "turn_on",
     "target": {"type": "entity", "name": "light.nappali"},
     "action": "on",
     "confidence": 0.95,
     "response": "Bekapcsoltam a nappali lámpát"
   }

4. HA Manager:
   - User HA instance port lookup
   - REST API call → user's HA instance
   
5. Response:
   - Generate natural response (LLM vagy template)
   - Store audit log
   - Return to Edge

Teljes latency: ~200-500ms (intent recognition + HA execution)
```

## 🔐 Biztonsági Arch

### Authentication Flow

```
Edge ──token──→ User API (verify JWT)
                    ↓
              Get user_id from token
                    ↓
              Load user's HA instance (port)
                    ↓
              Execute on per-user HA
```

### Token Encryption (HA API Tokens)

```
Plaintext HA token
      ↓
Fernet encryption (symmetric)
      ↓
Stored in database (ha_token_encrypted)
      ↓
Decrypted when needed for HA API call
```

## 🚀 Indítási Checklist

```bash
# 1. Environment beállítása
cp .env.example .env
# Módosítsd JWT_SECRET és ENCRYPTION_KEY

# 2. Docker Compose start
docker-compose up -d

# 3. Ollama modell betöltése
docker exec central-ollama ollama pull ministral-3:3b-instruct-2512-q4_K_M

# 4. Health checks
curl http://localhost:8000/api/v1/health  # User API
curl http://localhost:8001/api/v1/health  # HA Manager
curl http://localhost:11434/api/tags      # Ollama

# 5. Tesztelés
curl -X POST http://localhost:8000/api/v1/intent \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid",
    "device_id": "pi-1",
    "text": "Jó reggelt"
  }'
```

## 📚 Függőségek & Verzió Info

- **Python:** 3.11
- **FastAPI:** 0.104.1
- **SQLAlchemy:** 2.0.23
- **Pydantic:** 2.5.0
- **Ollama:** latest (GPU)
- **PostgreSQL:** 16-alpine
- **Redis:** 7-alpine
- **Docker:** 24.0+

## 🔜 Next Steps (Priority Order)

1. **Alembic migrations** - Structured DB management
2. **Audit logging** - Persist to database
3. **Session context** - Redis-based message history
4. **HA API integration** - Real intent execution
5. **Rate limiting** - DoS protection
6. **Error handling** - Graceful fallbacks
7. **Unit tests** - CI/CD pipeline
8. **Zabbix setup** - Production monitoring

## 🐛 Known Issues & Limitations

- [ ] HA Manager - DB persistence (currently mock)
- [ ] Session context tidak fully implemented
- [ ] Intent execution (→ user's HA) belum integrated
- [ ] No rate limiting yet
- [ ] Error codes standardization needed
- [ ] No request validation middleware
- [ ] Audit log sampling (tidak yet persisted)

## 📖 Referenciák

- [Central SRS](../docs/central_srs.md)
- [Ollama API Docs](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
