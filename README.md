# MicroPi Voice Control System

🎙️ Edge-Cloud architektúrájú, Wyoming protokoll alapú hangvezérelt okosotthon rendszer

## 📁 Projekt struktúra

```
MicroPi-System/
├── edge/                      # Raspberry Pi komponensek
│   ├── services/
│   │   ├── config/           # Home Assistant konfiguráció webes felület
│   │   ├── orchestrator/     # Központi koordinátor
│   │   ├── piper/            # Text-to-Speech (Wyoming-Piper)
│   │   ├── stt/              # Speech-to-Text (Wyoming-Whisper)
│   │   └── wakeword/         # Wake-word detektálás (Wyoming-OpenWakeWord)
│   ├── docker-compose.yml
│   └── README.md             # Edge telepítési útmutató
│
├── central/                   # Központi backend (tervezett)
│   ├── kubernetes/           # K8s manifesztumok
│   ├── terraform/            # Infrastruktúra kód
│   └── services/             # Backend szolgáltatások
│       ├── ha-manager/       # Home Assistant instance kezelő
│       ├── llm-service/      # LLM szolgáltatás (Ollama)
│       ├── admin-ui/         # Admin felület
│       ├── user-api/         # Felhasználói API
│       └── monitoring/       # Zabbix monitoring
│
├── shared/                    # Közös komponensek
│   └── wyoming-protocol/     # Wyoming protokoll definíciók
│
└── docs/                      # Dokumentáció
    ├── mikrobi_okosotthon_rendszer_srs.md
    └── LICENSE
```

## 🚀 Gyors kezdés

### Edge (Raspberry Pi)
A Raspberry Pi edge komponensek telepítéséhez és konfigurálásához lásd: [edge/README.md](edge/README.md)

### Central (Backend)
A központi backend implementációja fejlesztés alatt: [central/README.md](central/README.md)

## 🏗️ Architektúra

### Edge réteg (Raspberry Pi)
- **Wyoming-OpenWakeWord**: Wake-word detektálás ("Alexa" jelenleg, "Mikrobi" tervezett)
- **Wyoming-Whisper**: Speech-to-Text magyar nyelvvel
- **Wyoming-Piper**: Text-to-Speech magyar Anna hanggal
- **Orchestrator**: Szolgáltatások koordinálása, HA kommunikáció
- **Config Web**: Home Assistant konfiguráció webes felületen

### Központi réteg (Tervezett)
- **Home Assistant Manager**: Felhasználónként dedikált HA instance-ok
- **LLM Service**: Ollama alapú intelligens intent feldolgozás (Ministral 3 3B)
- **User Management**: Regisztráció, autentikáció, jogosultságok
- **Admin UI**: Rendszer adminisztráció és monitoring
- **Monitoring**: Zabbix alapú metrika gyűjtés és riasztás

## 🔄 Wyoming protokoll

A rendszer a [Wyoming protokollt](https://github.com/rhasspy/wyoming) használja:
- Egységes interfész voice assistant szolgáltatásokhoz
- TCP socket alapú, event-driven kommunikáció
- Home Assistant natív támogatás
- Moduláris és bővíthető architektúra

## 📖 Dokumentáció

- **[Szoftverkövetelmény-specifikáció (SRS)](docs/mikrobi_okosotthon_rendszer_srs.md)**: Teljes rendszerkövetelmények
- **[Edge telepítési útmutató](edge/README.md)**: Raspberry Pi setup és konfiguráció
- **[Central telepítési útmutató](central/README.md)**: Backend infrastruktúra (fejlesztés alatt)

## 🛠️ Fejlesztési állapot

### ✅ Implementált (Edge)
- Wyoming protokoll integráció
- Wake-word detektálás
- Magyar Speech-to-Text
- Magyar Text-to-Speech
- Home Assistant Conversation API integráció
- Docker Compose alapú deployment
- Webes konfigurációs felület

### 🚧 Fejlesztés alatt (Central)
- Kubernetes infrastruktúra
- Multi-tenant felhasználókezelés
- Ollama LLM integráció
- Terraform automatizáció
- Zabbix monitoring

### 📋 Tervezett
- Egyedi "Mikrobi" wake-word modell
- Multi-room támogatás
- Streaming STT
- Context-aware dialógusok
- Automatizmus létrehozás LLM-mel

## 📄 Licenc

MIT - Részletek: [docs/LICENSE](docs/LICENSE)

## 🤝 Közreműködés

A projekt két fő részből áll:
1. **Edge komponensek**: Raspberry Pi fejlesztés, Wyoming szolgáltatások
2. **Central backend**: Kubernetes, LLM, infrastruktúra

Mindkét rész független fejlesztést tesz lehetővé, közös protokoll és API megállapodásokkal.
