# Software Requirements Specification (SRS)
## MicroPi Central Backend - Voice Processing & Intent Execution

**Verzió:** 1.0  
**Dátum:** 2026. január 19.  
**Szerző:** Nagypal Márton (Diplomamunka)  
**Status:** Draft  

---

## 1. Bevezetés

### 1.1 Cél
Ez a dokumentum a **MicroPi Central Backend** szoftverkövetelményeit specifikálja. A rendszer az edge eszközöktől kapott felhasználói szöveget feldolgozza, Home Assistant LLM-en keresztül értelmezteti, parancsokat hajt végre, és választ küld vissza az edge-nek.

### 1.2 Alkalmazási terület
- **Felhasználó:** Diplomamunka projekt; teljesítmény-kritikus, biztonságos voice control pipeline
- **Helyreállíthatóság:** Home Assistant cloud/hybrid deployment
- **Nyelv:** Magyar nyelvű parancsok és válaszok

### 1.3 Definíciók és rövidítések
- **HA:** Home Assistant
- **LLM:** Large Language Model (Ollama-on futó)
- **Intent:** Parancs vagy kérdés a felhasználótól (szöveg)
- **Edge:** Raspberry Pi hang satellite eszköz
- **Wyoming:** TCP protokoll az edge-central kommunikációhoz
- **Per-user HA:** Dedikált Home Assistant instance felhasználónként
- **VAD:** Voice Activity Detection (edge-en)

---

## 2. Általános leírás

### 2.1 Rendszer perspektíva

```
Edge (Raspberry Pi)                    Central Backend                      Home Assistant
┌──────────────────┐                  ┌──────────────────┐                  ┌──────────────┐
│  Mikrofon        │                  │  User API        │                  │ Per-user HA  │
│  ↓              │                  │  ├─ /intent      │                  │ instances    │
│  Whisper (STT)  │──────────────────→ ├─ /execute      │─────────────────→│ (isolated)   │
│  ↓              │    szöveg+metadata │  └─ /chat       │   REST/WebSocket │              │
│  Hangszóró      │                  │                  │                  │              │
│  ↑              │                  │  LLM Service     │                  └──────────────┘
│  Piper (TTS)   │                  │  ├─ intent NER   │
│  ↑              │                  │  ├─ context mgmt │
│  Satellite      │                  │  └─ fallback     │
└──────────────────┘                  │                  │
                                      │  HA Manager      │
                                      │  ├─ lifecycle    │
                                      │  ├─ auth/token   │
                                      │  └─ isolation    │
                                      │                  │
                                      │  Monitoring      │
                                      │  ├─ audit log    │
                                      │  ├─ metrics      │
                                      │  └─ health check │
                                      └──────────────────┘
```

### 2.2 Termék funkciók

#### **Primer Pipeline (MVP)**
1. Edge → Central: Szöveg + metadata (felhasználó ID, device ID)
2. Central LLM Service: Intent felismerés, context kezelés
3. Central HA Manager: Parancs lefordítása, per-user HA instance-en futtatás
4. Válasz generálás és visszaküldés edge-nek
5. Edge: Piper TTS lejátssza a választ

#### **Másodlagos Funkciók**
- Audit logging (mely user, mely parancs, mikor, miért)
- Monitoring és health check
- Rate limiting per user
- Kontextus-megőrzés egy session alatt
- Fallback ha LLM/HA nem válaszol (timeout)

### 2.3 Felhasználó karakterisztikák
- **Elsődleges:** Végfelhasználó (otthonában hang kontrollal használja)
- **Másodlagos:** Admin (felhasználók kezelése, monitoring)
- **Tercier:** Diplomamunka evaluátorok (kód, dokumentáció, teljesítmény)

### 2.4 Korlátozások és Feltételezések
- **HA mindig elérhető** (SLA-val támogatva)
- **LLM mindig elérhető** (Ollama felügyelt vagy megbízható)
- **Hálózati késleltetés:** 50-200ms az edge és central között
- **Felhasználók száma (MVP):** Max 50 regisztrált, max 10 egyidejű
- **Egyidejűség:** Egy user egy időben egy parancs végrehajtása

---

## 3. Rendszer követelmények

### 3.1 Funkcionális követelmények

#### **3.1.1 User API – Intent feldolgozás**

**REQ-F-001:** A rendszernek el kell fogadnia POST `/api/v1/intent` lekéréseket az edge-től.
```
Input: {
  "user_id": "user123",
  "device_id": "rpi_living_room",
  "text": "Kapcsold be a nappali lámpát",
  "timestamp": "2026-01-19T14:30:00Z",
  "context": { "room": "living_room" }
}
Output: {
  "intent": "turn_on",
  "entity_id": "light.living_room",
  "response": "Bekapcsoltam a nappali lámpát",
  "status": "success"
}
```

**REQ-F-002:** Intent felismerés LLM-en keresztül történik (Ollama).
- Input: Szöveg + kontextus (előző parancsok, HA állapot)
- Output: Strukturált intent (entity, action, parameters)
- Timeout: 5 másodperc

**REQ-F-003:** Parancs végrehajtás per-user HA instance-en.
- Felhasználó autentikációja: JWT token
- HA tokenja per-user, külön key/secret-ben tárolva
- Izoláció: Egy user csak a saját HA instance-éhez fér hozzá

**REQ-F-004:** Intent-ből HA service call generálása.
- LLM kimenete: `{"service": "light.turn_on", "entity_id": "light.nappali", "brightness": 100}`
- HA Manager: Validáció, service hívás, error handling
- Válasz: `"Bekapcsoltam a nappali lámpát"`

**REQ-F-005:** Fallback ha HA/LLM timeout.
```
Response: {
  "status": "error",
  "message": "A Home Assistant jelenleg nem válaszol. Kérlek próbáld később.",
  "request_id": "req_12345"
}
```

**REQ-F-006:** Szessions kontextus megőrzés.
- Per-session: Max 10 előző üzenet megőrzése
- Session timeout: 5 perc inaktivitás után zárás
- Context: Előző parancsok, user preferences

**REQ-F-007:** Health check endpoint.
- `GET /health` → `{"status": "ok", "liveness": true}`
- `GET /ready` → `{"status": "ready", "ha": "connected", "llm": "connected"}`

#### **3.1.2 Home Assistant Manager**

**REQ-F-008:** Per-user HA instance kezelés.
- Regisztráció: User → HA instance automatikus létrehozása
- Token: Long-lived token generálása és biztonságos tárolása
- Update: Felhasználó HA konfiguráció frissítése (ha szükséges)
- Delete: User törlése → HA instance cleanup

**REQ-F-009:** HA API integration.
- Minimum HA verzió: 2024.12.0
- REST API: `/api/services/{domain}/{service}`
- WebSocket: Opcionális valós idejű státusz ha szükséges
- Timeout: 5 másodperc service call-onként

**REQ-F-010:** Hiba kezelés HA integráció szintjén.
- Reconnect: 3 próbálkozás, exponenciális backoff (1s, 2s, 4s)
- Circuit breaker: Ha 5 perc alatt 10+ hiba, bypass HA (fallback)
- Alerting: Audit log és monitoring

#### **3.1.3 LLM Service (Ollama)**

**REQ-F-011:** Intent NER (Named Entity Recognition) és generálás.
- Model: Ollama (pl. `mistral:7b` vagy `neural-chat`)
- Input: User szöveg + kontextus (HA entity-k, előző parancsok)
- Output: JSON intent és paraméterek
- Prompt template: Rendszerprompt meghatározza a validálódást

**REQ-F-012:** Kontextus menedzsment.
- Per-session memória: Rolling window (10 előző üzenet)
- Context injektálás: HA entity-k és szobák lekérdezése
- Prompt optimalizálás: Kiváló token felhasználás

**REQ-F-013:** Fallback ha LLM nem tudja feldolgozni.
```
{
  "intent": "ask",
  "entity_type": "general_question",
  "response": "Sajnálom, ezt a parancsot nem értem. Próbáld meg másképp megfogalmazni.",
  "confidence": 0.2
}
```

#### **3.1.4 Audit és Monitoring**

**REQ-F-014:** Audit napló minden intent-ről.
```
{
  "timestamp": "2026-01-19T14:30:00Z",
  "user_id": "user123",
  "device_id": "rpi_living_room",
  "input": "Kapcsold be a nappali lámpát",
  "intent": "turn_on",
  "entity_id": "light.nappali",
  "status": "success",
  "latency_ms": 1200,
  "llm_tokens": 45
}
```

**REQ-F-015:** Metrikák nyújtása Prometheus számára.
- Intent latency (p50, p95, p99)
- LLM token/sec
- HA service call success rate
- Active sessions per user

#### **3.1.5 Autentikáció és Hozzáférés-vezérlés**

**REQ-F-016:** JWT-alapú autentikáció.
- Issuer: Central backend
- Scope: per-user resource isolation
- Expiration: 1 óra (access token), 7 nap (refresh token)
- Claims: `user_id`, `device_id`, `roles`

**REQ-F-017:** Authorization.
- Role: `user` (saját resource) vagy `admin` (everybody)
- Per-resource check: A user csak a saját intentjeit/devicejeit kezelheti

---

### 3.2 Nem-funkcionális követelmények

#### **3.2.1 Teljesítmény**

**REQ-NF-001:** Intent end-to-end latency.
- Cél: p95 < 2000 ms (edge→central→HA→válasz)
- Lebontás:
  - Network: ~200 ms
  - LLM feldolgozás: ~800 ms
  - HA service call: ~300 ms
  - Válasz szerializáció: ~100 ms
- Mérik: Load testing, SLA monitoring

**REQ-NF-002:** Throughput.
- MVP: Min 10 egyidejű intent/sec
- Per-user: 1 intent/sec limit (rate limiting)

**REQ-NF-003:** Memória és CPU.
- Pod mem limit: 512 MB (LLM service), 256 MB (HA manager, user API)
- CPU limit: 1000m (LLM), 200m (HA manager, user API)

#### **3.2.2 Megbízhatóság**

**REQ-NF-004:** Availability.
- SLA: 99.5% (diplomamunka szint; ~3.6 óra downtime/hó)
- Health check: `/ready` endpoint 5 másodpercenként

**REQ-NF-005:** Graceful degradation.
- HA down: Intent fallback, hibaüzenet vissza edge-nek
- LLM down: Intent fallback (simple rule-based)
- Nem crash: Minden exception caught és logged

**REQ-NF-006:** Adatintegritás.
- Audit log: Immutable (append-only)
- User session: Persistent (Redis/PostgreSQL), crash után helyreállít

#### **3.2.3 Biztonság**

**REQ-NF-007:** Titkosítás in-transit.
- TLS 1.3: Összes külső API (edge→central, central→HA, central→Ollama)
- Cert: Self-signed vagy CA-ből (prod)

**REQ-NF-008:** Titok kezelés.
- HA token: K8s Secret vagy environment variable (encrypted at rest)
- JWT secret: Secure random, >256 bit
- Jelszavak: bcrypt/argon2, salted

**REQ-NF-009:** Input validáció.
- Szöveg hossz: Max 1000 karaktert
- Intent: Whitelist service-k (pl. `light.turn_on`, `climate.set_temperature`)
- Entity ID: Pattern match, nem tetszőleges SQL/code

**REQ-NF-010:** Audit trail.
- Log minden intent, parancs, auth event
- Megőrzés: 90 nap
- Hozzáférés: Csak admin és a user saját logjait

#### **3.2.4 Karbantarthatóság és Üzemeltethetőség**

**REQ-NF-011:** Strukturált logolás.
- Format: JSON (timestamp, level, message, context)
- Levels: DEBUG, INFO, WARN, ERROR
- Correlation ID: Request ID propagálódik log-okon keresztül

**REQ-NF-012:** Monitoring és alerting.
- Prometheus metrics: Intent latency, error rate, LLM availability
- Alerts: LLM down, HA down per user, latency spike (>3s p95)

**REQ-NF-013:** Konfigurálhatóság.
- Environment variables: Felsorolt alul
- ConfigMap: Kubernetes env-ből
- Feature flags: Fallback módok, debug logging

**REQ-NF-014:** Verziózás és frissítés.
- Semantic versioning: API v1, v2, etc.
- Backward compatibility: Min 1 major verzió áthaladás
- Blue-green deploy: Zérus-downtime frissítés

---

## 4. Külső Interfészek

### 4.1 Edge → Central (REST/WebSocket)

```
POST /api/v1/intent
{
  "user_id": "user123",
  "device_id": "rpi_living_room",
  "text": "Kapcsold be a nappali lámpát",
  "session_id": "sess_xyz",
  "timestamp": "2026-01-19T14:30:00Z"
}

Response 200:
{
  "request_id": "req_abc123",
  "intent": "turn_on",
  "entity_id": "light.nappali",
  "response": "Bekapcsoltam a nappali lámpát.",
  "status": "success",
  "latency_ms": 1200
}

Response 500:
{
  "request_id": "req_abc123",
  "status": "error",
  "message": "A Home Assistant jelenleg nem válaszol.",
  "error_code": "HA_TIMEOUT"
}
```

### 4.2 Central → Home Assistant (REST API)

```
Authorization: Bearer <per-user-token>

POST http://user_ha_instance:8123/api/services/light/turn_on
{
  "entity_id": "light.nappali",
  "brightness": 255
}

Response 200:
[ { "entity_id": "light.nappali", "state": "on" } ]
```

### 4.3 Central → Ollama (REST API)

```
POST http://ollama:11434/api/generate
{
  "model": "mistral:7b",
  "prompt": "User: Kapcsold be a nappali lámpát\nSystem: ...",
  "stream": false
}

Response:
{
  "response": "{\"intent\": \"turn_on\", \"entity_id\": \"light.nappali\"}",
  "context": [...]
}
```

---

## 5. Rendszer Architektúra

### 5.1 Komponensek és Felelősségek

| Komponens | Felelősség | API Port |
|-----------|-----------|----------|
| User API | Intent fogadása, session mgmt, auth | 8000 |
| HA Manager | HA instance lifecycle, token, service calls | (interno) |
| LLM Service | Intent NER, prompt mgmt, Ollama kliens | (interno) |
| Audit Service | Logging, monitoring metrics | (interno) |
| PostgreSQL | User, session, audit data | 5432 |
| Redis | Session cache, rate limiting | 6379 |
| Ollama | LLM inference | 11434 |

### 5.2 Üzemanyagok és Könyvtárszerkezet

```
central/
├── services/
│   ├── user-api/
│   │   ├── Dockerfile
│   │   ├── main.py              # FastAPI app
│   │   ├── app/
│   │   │   ├── models.py        # Pydantic schemas
│   │   │   ├── routes.py        # /api/v1/intent, /health, /ready
│   │   │   ├── auth.py          # JWT, RBAC
│   │   │   └── dependencies.py  # DI
│   │   ├── requirements.txt
│   │   └── tests/
│   │
│   ├── ha-manager/
│   │   ├── Dockerfile
│   │   ├── main.py              # Service (injected)
│   │   ├── ha_client.py         # HA REST client + caching
│   │   ├── lifecycle.py         # Create/update/delete instance
│   │   └── requirements.txt
│   │
│   ├── llm-service/
│   │   ├── Dockerfile
│   │   ├── main.py              # Service (injected)
│   │   ├── ollama_client.py     # Ollama kliens
│   │   ├── prompt_builder.py    # Prompt templating
│   │   ├── intent_parser.py     # JSON parsing, validation
│   │   └── requirements.txt
│   │
│   └── monitoring/
│       └── prometheus_exporter.py
│
├── kubernetes/
│   ├── base/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   ├── secret.yaml
│   │   └── hpa.yaml
│   └── overlays/
│       ├── dev/
│       │   ├── kustomization.yaml
│       │   └── patch-*.yaml
│       └── prod/
│           ├── kustomization.yaml
│           └── ingress.yaml
│
├── terraform/
│   ├── modules/
│   │   ├── k8s_cluster/
│   │   ├── postgres/
│   │   └── ollama/
│   └── environments/
│       ├── dev/
│       │   ├── main.tf
│       │   └── vars.tf
│       └── prod/
│           ├── main.tf
│           └── vars.tf
│
├── docker-compose.yml           # Local dev
├── .env.example                 # Env template
└── README.md                    # Deployment guide
```

---

## 6. API Specifikáció (OpenAPI 3.0)

Külön dokumentum: `central/openapi.yaml`

Kulcs végpontok:
- `POST /api/v1/intent` – Intent feldolgozás
- `GET /api/v1/health` – Health check
- `GET /api/v1/ready` – Readiness check (deps check)
- `POST /api/v1/auth/login` – Bejelentkezés (token)
- `POST /api/v1/auth/refresh` – Token refresh

---

## 7. Adatmodell

### 7.1 Entitások

```sql
-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,  -- argon2
  ha_instance_url VARCHAR(255),
  ha_token_encrypted BYTEA,             -- KMS-protected
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  role VARCHAR(20) DEFAULT 'user'       -- 'user', 'admin'
);

-- Sessions
CREATE TABLE sessions (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  device_id VARCHAR(255),
  created_at TIMESTAMP NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  context JSONB,                         -- Rolling window of prev messages
  PRIMARY KEY (id)
);

-- Audit Log
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  timestamp TIMESTAMP NOT NULL,
  user_id UUID NOT NULL REFERENCES users(id),
  device_id VARCHAR(255),
  input_text TEXT NOT NULL,
  intent JSONB NOT NULL,                -- {"intent": "turn_on", "entity_id": "..."}
  ha_response JSONB,                    -- HA válasza
  status VARCHAR(20),                   -- 'success', 'error', 'timeout'
  latency_ms INT,
  llm_tokens INT,
  error_message TEXT,
  request_id VARCHAR(255) UNIQUE,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 8. Telepítés és Deployment

### 8.1 Előfeltételek

#### **Fejlesztés (Docker Compose)**
- Docker Engine (20.10+)
- Docker Compose (2.0+)
- Python 3.10+
- PostgreSQL 14
- Redis 7
- Ollama (pull `mistral:7b`)

#### **Produktion (Kubernetes)**
- Kubernetes 1.25+
- kubectl
- Helm 3.0+ (opcionális)
- Ingress Controller (nginx)
- Storage provisioner (local/NFS)

### 8.2 Gyors indítás (Dev)

```bash
# 1. Clone és env
cd central
cp .env.example .env

# 2. Docker Compose
docker-compose up -d

# 3. Init DB
docker-compose exec user-api python -m alembic upgrade head

# 4. Test
curl http://localhost:8000/health
```

### 8.3 Produktion (Kubernetes)

```bash
# 1. Build és push
docker build -t myregistry/central:1.0.0 .
docker push myregistry/central:1.0.0

# 2. Deploy
kubectl apply -k kubernetes/overlays/prod/

# 3. Verify
kubectl rollout status deployment/central-user-api
kubectl logs -l app=central
```

---

## 9. Tesztelési Stratégia

### 9.1 Unit Teszt

- HA Manager: Token kezelés, API call mocking
- LLM Service: Prompt builder, JSON parser
- Auth: JWT encoding/decoding

### 9.2 Integration Teszt

- Intent end-to-end: Mock HA + LLM
- Audit log: DB insert/query
- Rate limiting: Redis interaction

### 9.3 E2E / Smoke Test

- Staging: Valós HA + LLM (de test intent-ek)
- Canary: Production traffic 5%-a az új verzióra
- Rollback: Ha error rate > 1% vagy latency p95 > 3s

### 9.4 Load Testing

- Tool: k6 vagy Apache JMeter
- Skenárió: 50 user, 10 intent/sec, 5 perc
- Assert: p95 < 2000ms, error rate < 0.1%

---

## 10. Biztonsági követelmények

- **Transport:** TLS 1.3 (minden endpoint)
- **Auth:** JWT (RS256 vagy HS256)
- **Data at rest:** PostgreSQL encrypted (pgcrypto vagy KMS)
- **Secrets:** K8s Secret, HA token szeparált
- **Input validation:** Whitelist (entity IDs, service names)
- **Audit:** Immutable log, 90 nap megőrzés
- **GDPR:** User data export, deletion, consent log

---

## 11. Monitoring és SLA

### 11.1 KPI-k

| Metrika | Cél | Riasztás |
|---------|-----|----------|
| Intent latency p95 | <2000 ms | >2500 ms |
| LLM availability | 99.5% | <99% |
| HA availability (per user) | 99.5% | <99% |
| Error rate | <0.5% | >1% |
| Active sessions | <100 | >150 (scale up) |

### 11.2 Dashboardok

- Grafana: Intent latency, error rate, LLM tokens
- Zabbix: HA instance health per user
- Custom: Per-user usage report

---

## 12. Fejlesztési Fázisok

### **Fázis 1 (MVP – Hét 1-4)**
- [ ] User API + JWT auth
- [ ] HA Manager (create instance, token gen)
- [ ] LLM Service (Ollama integration)
- [ ] PostgreSQL + Redis
- [ ] Audit log
- [ ] Docker Compose local dev
- [ ] Smoke testing

### **Fázis 2 (Prod Ready – Hét 5-8)**
- [ ] Kubernetes manifests
- [ ] Monitoring (Zabbix/Prometheus)
- [ ] Load testing + optimization
- [ ] Integration testing
- [ ] Documentation (OpenAPI, deploy, runbook)
- [ ] Thesis draft

### **Fázis 3 (Polish – Hét 9-12)**
- [ ] Performance tuning
- [ ] Security audit
- [ ] Edge→Central integration testing
- [ ] Final testing és UAT
- [ ] Thesis finalization

---

## 13. Kockázatok és Mitigáció

| Kockázat | Valószínűség | Hatás | Mitigáció |
|----------|------------|-------|----------|
| LLM latency >3s | Közepes | Magas | Prompt cache, model quantize |
| HA instance down | Alacsony | Magas | Fallback msg, health check |
| Network lag | Közepes | Közepes | Timeout + retry, compression |
| User growth > MVP | Alacsony | Magas | Horizontal scale (HPA) |
| Ollama model pin | Alacsony | Magas | Version lock, mirror host |

---

## 14. Jóváhagyás és Verzió

| Szerepkör | Név | Dátum | Status |
|-----------|-----|-------|--------|
| Szerző | Nagypal Márton | 2026.01.19 | Draft |
| Témavezető | [Név] | | Pending |
| TA | [Név] | | Pending |

---

## Függelék: Environment Változók

```bash
# Central Backend
CENTRAL_PORT=8000
CENTRAL_ENV=development  # development, staging, production

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/central
DATABASE_POOL_SIZE=10

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=20

# JWT
JWT_SECRET=your-256-bit-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=1
REFRESH_TOKEN_EXPIRATION_DAYS=7

# LLM / Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b
LLM_TIMEOUT_SECONDS=5
LLM_CONTEXT_WINDOW=10

# HA (per-user token später a DB-ben)
HA_DEFAULT_URL=http://localhost:8123
HA_TIMEOUT_SECONDS=5
HA_RETRY_COUNT=3

# Audit
AUDIT_RETENTION_DAYS=90
AUDIT_BATCH_INSERT=100

# Monitoring
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO

# Security
RATE_LIMIT_PER_USER=10  # requests/minute
RATE_LIMIT_GLOBAL=100   # requests/second
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Feature Flags
FEATURE_LLM_CACHE=true
FEATURE_HA_FALLBACK=true
DEBUG_MODE=false
```

---

**Document Change Log:**

| Verzió | Dátum | Módosítás |
|--------|-------|----------|
| 0.1 | 2026.01.19 | Initial draft |

