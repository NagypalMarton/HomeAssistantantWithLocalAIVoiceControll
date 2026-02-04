# Central Backend - MicroPi Voice Control Service

[![Central Backend CI](https://github.com/NagypalMarton/HomeAssistantantWithLocalAIVoiceControll/actions/workflows/central-ci.yml/badge.svg)](https://github.com/NagypalMarton/HomeAssistantantWithLocalAIVoiceControll/actions/workflows/central-ci.yml)

🚀 **Edge szöveg feldolgozása, Home Assistant végrehajtás, válasz vissza**

## Áttekintés

A **Central Backend** az edge (Raspberry Pi) eszközöktől kapott felhasználói szövegeket feldolgozza:

1. **Intent feldolgozás:** Ollama LLM-en keresztül (ministral-3:3b) felismeri a parancsot
2. **Végrehajtás:** Per-user Home Assistant instance-en futtatja a parancsot
3. **Válasz:** Természetes nyelvű választ küld vissza az edge-nek

Ez egy **diplomamunka projekt**, amely szakmailag konfigurálható, tesztelt és dokumentált.

## Aktuális Architektúra

### Service-ek

```
central-postgres      → PostgreSQL adatbázis (user, session, audit_log)
central-redis         → Redis cache (session context)
central-ollama        → Ollama LLM (GPU támogatás)
central-user-api      → FastAPI (intent feldolgozás)
central-ha-manager    → Docker-alapú HA instance menedzsment
central-prometheus    → Prometheus monitoring (opcionális)
```

### Komponensek részletezése

#### 1. **User API Service** (port 8000)
- Intent feldolgozás pipeline
- User autentikáció (JWT)
- Session context kezelés
- HA Manager API hívások
- Audit logging
- API endpoints:
  - `POST /api/v1/auth/register` - Regisztráció
  - `POST /api/v1/auth/login` - Bejelentkezés
  - `POST /api/v1/intent` - Intent feldolgozás
  - `GET /api/v1/health` - Health check

#### 2. **HA Manager Service** (port 8001)
- Per-user Docker-alapú HA instance lifecycle management
- Automatikus HA container létrehozás regisztrációkor
- Port allokáció (8200-8300)
- Volumen kezelés
- Container health monitoring
- API endpoints:
  - `POST /api/v1/ha/instance` - HA instance létrehozás
  - `GET /api/v1/ha/instance/{user_id}` - HA instance lekérdezés
  - `DELETE /api/v1/ha/instance/{user_id}` - HA instance törlés
  - `GET /api/v1/ha/instance/{user_id}/status` - Status lekérdezés

#### 3. **Ollama LLM Service** (port 11434)
- **Modell:** `ministral-3:3b-instruct-2512-q4_K_M`
- **GPU accelerated** (NVIDIA, 4GB vRAM)
- **Chat template:** Ministral-3 natív format (`[SYSTEM_PROMPT]...[/SYSTEM_PROMPT]`, `[INST]...[/INST]`)
- **Temperature:** 0.15 (determinisztikus output)
- **Context window:** Utolsó 10 üzenet
- Intent felismerés JSON outputtal
- Magyar nyelvű prompt engineering
- Timeout: 30 másodperc

#### 4. **Adatbázis** (port 5432)
- PostgreSQL 16
- Táblák:
  - `users` - felhasználók (email, ha_token_encrypted, role)
  - `sessions` - aktív session-ök (context window)
  - `audit_log` - parancs históriája (input, intent, HA response, latency)
  - `ha_instances` - per-user HA container metadatai

#### 5. **Redis Cache** (port 6379)
- Session context (rolling window)
- Token blacklist (logout)
- Rate limiting counters

## Technológiai Stack

### Backend
- **Python 3.11**
- **FastAPI** - REST API framework
- **SQLAlchemy** - ORM (async)
- **asyncpg** - PostgreSQL async driver
- **Pydantic** - Data validation
- **python-jose** - JWT handling
- **cryptography** - Token encryption (Fernet)

### Infrastruktúra
- **Docker Compose** - Service orchestration (dev/staging)
- **PostgreSQL 16** - Relational database
- **Redis 7** - Cache & sessions
- **Ollama** - LLM inference (GPU)

### Monitoring
- **Prometheus** - Metrics collection
- **Structlog** - Structured JSON logging

## Telepítés & Indítás

### Előfeltételek

- **Docker Engine** (GPU support: NVIDIA Docker Runtime)
- **Docker Compose** v2.0+
- **4GB+ VRAM GPU** (Ollama/Ministral-3 futtatásához)
- **4GB RAM minimum** (Docker containers)
- **20GB szabad tárhelyre** (HA instances + Ollama modellek)

### Lépések

1. **Repository klónozása**
```bash
cd central
```

2. **Automatikus indítás (egyszerű módszer)**

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**Windows (PowerShell):**
```powershell
.\start.ps1
```

Ez a script automatikusan:
- ✅ Létrehozza a `.env` fájlt ha nincs
- ✅ Generál biztonságos `JWT_SECRET` és `ENCRYPTION_KEY` kulcsokat
- ✅ Elindítja az összes Docker service-t
- ✅ Ellenőrzi a health check-eket

**Vagy manuális indítás:**
```bash
# 1. Environment beállítása (első alkalommal)
docker-compose --profile setup run --rm init

# 2. Services indítása
docker-compose up -d
```

3. **Ollama modell betöltése**
```bash
docker exec central-ollama ollama pull ministral-3:3b-instruct-2512-q4_K_M
```

4. **Service-ek ellenőrzése**
```bash
docker-compose ps
docker-compose logs -f user-api
```

5. **Health check**
```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/api/v1/health
curl http://localhost:11434/api/tags
```

## API Végpontok

### Intent Processing
```
POST /api/v1/intent
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "user_id": "uuid",
  "device_id": "raspberry-pi-1",
  "text": "Kapcsold be a nappali lámpát",
  "session_id": "optional-session-uuid"
}

Response:
{
  "request_id": "uuid",
  "intent": "turn_on",
  "entity_id": "light.nappali",
  "response": "Bekapcsoltam a nappali lámpát.",
  "status": "success",
  "confidence": 0.95,
  "latency_ms": 245
}
```

### HA Instance Management
```
POST /api/v1/ha/instance
{
  "user_id": "uuid"
}

Response:
{
  "user_id": "uuid",
  "container_id": "abc123...",
  "container_name": "ha-user-12345678",
  "status": "running",
  "host_port": 8200,
  "timezone": "Europe/Budapest"
}
```

## Fejlesztési Státusz

### Implementálva ✅
- [x] Docker Compose setup (GPU support)
- [x] User API alapstruktúra
- [x] Ollama LLM service integration
- [x] Intent processing pipeline (LLM)
- [x] Token encryption (Fernet)
- [x] HA Manager service alapstruktúra
- [x] Docker container management
- [x] PostgreSQL + Redis setup

### TODO 🚧
- [ ] Alembic migrations
- [ ] HA Manager - User API integráció
- [ ] Audit logging (DB persistence)
- [ ] Session context management (Redis)
- [ ] HA parancs végrehajtás integrációja
- [ ] Rate limiting implementáció
- [ ] Error handling & fallbacks
- [ ] Unit & integration tests
- [ ] Prometheus metrics refinement
- [ ] Performance optimization

## Biztonsági Aspektusok

- ✅ JWT-alapú autentikáció
- ✅ Token encryption (Home Assistant API tokenekhez)
- ✅ SQL injection védelem (SQLAlchemy parameterization)
- ✅ CORS configured
- ✅ Per-user HA instance izoláltsága (Docker network)
- 🚧 Rate limiting
- 🚧 Request validation
- 🚧 Audit trail

## Monitoring & Logging

### Strukturált Logging
- **Format:** JSON
- **Library:** structlog
- **Szintek:** INFO, WARNING, ERROR
- **Mezők:** timestamp, request_id, user_id, latency_ms, error

### Prometheus Metrikák
- Request latency
- Request count by endpoint
- Error rate
- LLM response time
- Database query duration
- Service health checks
- Container resource usage
- Database metrics

## Fejlesztői Útmutató

### Helyi fejlesztés

1. **Python venv**
```bash
cd services/user-api
python -m venv venv
source venv/bin/activate  # Linux/Mac
# vagy: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **Database setup**
```bash
# Docker postgres start
docker-compose up -d postgres redis ollama

# Migrations (később Alembic)
# sqlalchemy models automatikusan létrehoznak táblákat init_db-vel
```

3. **Local development**
```bash
cd services/user-api
uvicorn main:app --reload --port 8000
```

### Testing

```bash
# Unit tests
pytest services/user-api/tests/ -v

# Coverage
pytest --cov=app services/user-api/tests/
```

## Troubleshooting

### Ollama GPU error
```
Error: CUDA device not found
→ Ellenőrizd az NVIDIA Docker Runtime-ot: docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

### Port már foglalt
```
docker-compose down
# vagy: lsof -i :8000 / netstat -tulpn
```

### Database connection error
```
docker-compose logs postgres
# Check: POSTGRES_USER, POSTGRES_PASSWORD env vars
```

## Kapcsolódó Dokumentumok

- [Szoftverkövetelmény-specifikáció](../docs/central_srs.md)
- [Edge telepítési útmutató](../edge/README.md)
- [Projekt struktúra](../README.md)
- [Zabbix monitoring](./monitoring/ZABBIX.md) (később)

## Közreműködés

A central backend fejlesztése folyamatban. Kérdések, PR-ok és javaslatok várhatóak! 🚀

