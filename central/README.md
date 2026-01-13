# Central Backend - MicroPi System

🏗️ Központi backend infrastruktúra (Fejlesztés alatt)

## Áttekintés

A központi backend felelős a következőkért:
- Felhasználókezelés és autentikáció
- Home Assistant instance-ok létrehozása és kezelése felhasználónként
- LLM-alapú intelligens intent feldolgozás (Ollama + Ministral 3 3B)
- Rendszer monitoring és adminisztráció
- API szolgáltatások az edge eszközök számára

## Tervezett architektúra

### Komponensek

#### 1. Home Assistant Manager
- Felhasználónként dedikált HA instance-ok
- Automatikus létrehozás regisztrációkor
- Lifecycle management (create, update, delete)
- REST API hozzáférés biztosítása

#### 2. LLM Service (Ollama)
- Ministral 3 3B modell
- Kontextuális parancsok feldolgozása
- Home Assistant állapot lekérdezés
- Intent generálás és végrehajtás
- Request-szintű context izolálás

#### 3. User Management API
- Felhasználói regisztráció
- Autentikáció és jogosultságok
- HA instance hozzárendelés
- Profil kezelés

#### 4. Admin UI
- Felhasználók kezelése
- Rendszer metrikák
- Service health checks
- Konfiguráció menedzsment

#### 5. Monitoring (Zabbix)
- Kubernetes cluster monitoring
- HA instance health checks
- LLM metrikák (response time, token usage)
- Edge eszköz monitoring (HTTP exportereken keresztül)

## Technológiai stack

### Infrastruktúra
- **Kubernetes**: Container orchestration
- **Terraform**: Infrastructure as Code
- **Docker**: Konténerizáció
- **Helm**: Kubernetes package management

### Backend szolgáltatások
- **Python FastAPI**: REST API-k
- **PostgreSQL**: Felhasználói adatok, konfiguráció
- **Redis**: Session cache, queue
- **Ollama**: LLM inference

### Monitoring és logging
- **Zabbix**: Metrika gyűjtés és riasztás
- **Prometheus**: (opcionális) Kubernetes metrikák
- **Grafana**: (opcionális) Dashboard-ok

## Könyvtárstruktúra (tervezett)

```
central/
├── kubernetes/
│   ├── base/                 # Base manifests
│   ├── overlays/             # Kustomize overlays
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   └── helm/                 # Helm charts
│
├── terraform/
│   ├── modules/
│   │   ├── k8s-cluster/
│   │   ├── ha-instance/
│   │   └── networking/
│   └── environments/
│       ├── dev/
│       └── prod/
│
├── services/
│   ├── ha-manager/
│   │   ├── Dockerfile
│   │   ├── app/
│   │   └── requirements.txt
│   │
│   ├── llm-service/
│   │   ├── Dockerfile
│   │   ├── app/
│   │   └── requirements.txt
│   │
│   ├── user-api/
│   │   ├── Dockerfile
│   │   ├── app/
│   │   └── requirements.txt
│   │
│   ├── admin-ui/
│   │   ├── Dockerfile
│   │   ├── frontend/
│   │   └── package.json
│   │
│   └── monitoring/
│       └── zabbix/
│
├── scripts/
│   ├── deploy.sh
│   └── setup-cluster.sh
│
└── README.md
```

## Telepítés (tervezett)

### Előfeltételek
- Kubernetes cluster (v1.25+)
- kubectl telepítve
- Terraform v1.5+
- GPU node(ok) az LLM futtatásához

### Lépések

1. **Infrastruktúra létrehozása**
```bash
cd terraform/environments/prod
terraform init
terraform plan
terraform apply
```

2. **Kubernetes szolgáltatások telepítése**
```bash
cd kubernetes
kubectl apply -k overlays/prod/
```

3. **Zabbix monitoring konfigurálása**
```bash
cd services/monitoring/zabbix
./setup-monitoring.sh
```

## API végpontok (tervezett)

### User Management
- `POST /api/v1/auth/register` - Felhasználó regisztráció
- `POST /api/v1/auth/login` - Bejelentkezés
- `GET /api/v1/user/profile` - Profil lekérdezés
- `GET /api/v1/user/ha-instance` - HA instance URL

### HA Manager
- `POST /api/v1/ha/instance` - HA instance létrehozás
- `GET /api/v1/ha/instance/{user_id}` - HA instance lekérdezés
- `DELETE /api/v1/ha/instance/{user_id}` - HA instance törlés

### LLM Service
- `POST /api/v1/llm/intent` - Intent feldolgozás
- `POST /api/v1/llm/automation` - Automatizmus generálás

## Fejlesztési státusz

- [ ] Kubernetes cluster setup
- [ ] Terraform modulok
- [ ] HA Manager service
- [ ] User Management API
- [ ] LLM Service integráció
- [ ] Admin UI
- [ ] Zabbix monitoring
- [ ] CI/CD pipeline
- [ ] Dokumentáció

## Biztonsági szempontok

- TLS/SSL minden kommunikációhoz
- JWT-alapú autentikáció
- Role-based access control (RBAC)
- Felhasználói adatok titkosítása
- Network policies Kubernetes-ben
- Secrets management (Kubernetes Secrets / Vault)

## Kapcsolódó dokumentumok

- [Szoftverkövetelmény-specifikáció](../docs/mikrobi_okosotthon_rendszer_srs.md)
- [Edge telepítési útmutató](../edge/README.md)
- [Projekt struktúra](../README.md)

## Közreműködés

A central backend fejlesztése folyamatban. Kérdések és javaslatok várhatóak!
