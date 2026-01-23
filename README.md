# MicroPi Voice Control System

🎙️ Edge-Cloud architektúrájú, Wyoming protokoll alapú hangvezérelt okosotthon rendszer

## TL;DR Edge indítás (Raspberry Pi)
- `cd edge && ./start.sh` – add meg a HA URL-t és tokent (első futáskor), automatikusan elindul a Docker stack
- Home Assistant → Add Integration → Wyoming → host: `<pi-ip>`, port: `10700`

## 📁 Projekt struktúra

```
MicroPi-System/
├── edge/                              # Raspberry Pi komponensek
│   ├── docker-compose.yml            # Wyoming stack definíció
│   ├── setup.sh                      # Automatikus konfiguráló script
│   ├── ha_healthwatch_enhanced.sh    # HA elérhetőség figyelő (ASR-alapú)
│   ├── ha_healthwatch_enhanced.md    # Health watcher dokumentáció
│   ├── .env                          # Környezeti változók (HA URL, token, stb.)
│   ├── oww-models/                   # OpenWakeWord modellek (hey_jarvis)
│   ├── oww-data/                     # Wake word training adatok
│   ├── piper-data/                   # Piper TTS modellek (hu_HU-imre-medium)
│   ├── whisper-data/                 # Whisper STT modellek (tiny-int8)
│   ├── tts-cache/                    # TTS cache és alert WAV fájlok
│   ├── SRS.md                        # Edge Software Requirements Specification
│   └── README.md                     # Edge telepítési útmutató
│
├── central/                           # Központi backend (fejlesztés alatt)
│   ├── docker-compose.yml            # Backend services (tervezett)
│   ├── services/
│   │   └── user-api/                 # Felhasználói API (részben implementált)
│   └── README.md                     # Central telepítési útmutató
│
├── docs/                              # Dokumentáció
│   ├── mikrobi_okosotthon_rendszer_srs.md  # Teljes rendszer SRS
│   └── LICENSE                       # MIT licenc
│
├── .github/                           # CI/CD workflows
│   └── workflows/                    # GitHub Actions
│
└── README.md                          # Projekt főoldal (ez a fájl)
```

## 🚀 Gyors kezdés

### Edge (Raspberry Pi)
A Raspberry Pi edge komponensek telepítéséhez és konfigurálásához lásd: [edge/README.md](edge/README.md)

### Central (Backend)
A központi backend implementációja fejlesztés alatt: [central/README.md](central/README.md)

## 🏗️ Architektúra

### Edge réteg (Raspberry Pi)
- **Wyoming-OpenWakeWord**: Wake-word detektálás ("Hey Jarvis" jelenleg, "Mikrobi" tervezett)
- **Wyoming-Whisper**: Speech-to-Text magyar nyelvvel (offline, tiny-int8)
- **Wyoming-Piper**: Text-to-Speech magyar Imre hanggal (offline, medium quality)
- **Wyoming Satellite**: Mikrofon/hangszóró koordináció, pipeline management
- **Enhanced HA Health Watcher**: Intelligens HA elérhetőség figyelés ASR-alapú riasztással

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
- Wake-word detektálás ("Hey Jarvis")
- Magyar Speech-to-Text (offline, Whisper tiny-int8)
- Magyar Text-to-Speech (offline, Piper hu_HU-imre-medium)
- Home Assistant Conversation API integráció
- Docker Compose alapú deployment
- Enhanced HA Health Watcher:
  - ASR esemény utáni azonnali HA ellenőrzés
  - Kapcsolatvesztés azonnali észlelése
  - Intelligens riasztási módok (once/repeat)
  - Piper TTS alapú hangos riasztás

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
