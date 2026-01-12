# MicroPiSoundControl

🎙️ Docker-alapú hangvezérelt asszisztens rendszer Raspberry Pi 4-re, Python szolgáltatásokkal:
- **Wake word detektor** ("Mikrobi" ébresztőszó)
- **Whisper STT** (Speech-to-Text, magyar + angol)
- **Piper TTS** (Text-to-Speech, magyar + angol hangok)
- **Config weboldal** a FORWARD_URL konfigurálásához
- **Orchestrator** koordináció: felvétel → transzkripció → feldolgozás → válasz lejátszása

## 🚀 Gyors indítás

### 1. Docker Compose indítása

```bash
cd /home/nagypal.marton/Documents/MicroPiSoundControl
docker compose build
docker compose up
```

**Első indulás ideje:** ~5-10 perc (modell letöltések: Whisper ~700MB, Piper ~100MB)

### 2. Konfiguráció beállítása

Nyisd meg a konfigurációs weboldalt:
```
http://localhost:8000
```

vagy Raspberry Pi IP címével:
```
http://<raspberry-pi-ip>:8000
```

### 3. FORWARD_URL megadása

Add meg a szöveg feldolgozásáért felelős szolgáltatás URL-jét (kötelező):

**Példák:**
- `http://localhost:8080/handle` - Helyi NLP service
- `http://chatgpt-wrapper:5000/chat` - ChatGPT API wrapper
- `http://homeassistant:8123/api/webhook/mikrobi` - Home Assistant
- `http://192.168.1.100:3000/process` - Távoli szerver

**Fontos:** A szolgáltatás protokollja:
```json
Request:  POST <FORWARD_URL> {"text": "kapcsold be a lámpát"}
Response: 200 OK {"text": "Rendben, bekapcsolom a lámpát"}
```

### 4. Használat

Miután a konfiguráció mentve → az orchestrator automatikusan elindul!

**Parancsadás:**
1. Mondd: **"Mikrobi"** (ébresztőszó)
2. Várj ~0.5 másodpercet
3. Add ki a parancsot (max 5 másodperc)
4. A rendszer feldolgozza és válaszol hangon keresztül

## 📐 Architektúra

### Szolgáltatások

#### 1. **Config Service** (Port: 8000)
- Weboldal alapú konfiguráció
- FORWARD_URL beállítása kötelező az orchestrator indulásához
- Konfiguráció mentése: `/app/config/forward_url.json` (Docker volume)
- REST API: `GET/POST /api/config`, `GET /health`
⚙️ Környezeti Változók

A Docker Compose alapértelmezett értékekkel indul, de testre szabható:

```bash
# STT konfiguráció (Raspberry Pi 4 ajánlott: base vagy tiny)
export STT_MODEL_SIZE="base"      # tiny/base/small/medium/large
export STT_LANGUAGE="hu"          # hu/en (fix, nincs auto-detect)

# Wake word (opcionális: egyedi modell)
export WAKEWORD_MODEL_PATH=""     # pl: /models/mikrobi.oww
export WAKEWORD_WORD="mikrobi"

# Felvétel maximum idő
export RECORD_SECONDS="5"

# Audio eszköz helye (opcionális)
export SAMPLE_RATE="16000"        # VAD optimalizálva 16000 Hz-re

# Config & Voice útvonalak (opcionális)
export CONFIG_DIR="/app/config"
export VOICES_DIR="/app/voices"

# Majd indítás
docker compose up
```

**FONTOS:** A `FORWARD_URL` **NEM környezeti változó**! A config weboldalon (http://localhost:8000) kell beállítani!

**Magic Constants (kódban definiálva):**
- `HTTP_TIMEOUT = 30s` - STT, TTS, Forward request timeout
- `VAD_AGGRESSIVENESS = 2` - Voice Activity Detection szenzitivitása (0-3)
- `OWW_SCORE_THRESHOLD = 0.5` - OpenWakeWord detektálás küszöb
- `ENERGY_THRESHOLD = 0.2` - STT-alapú wake word energia küszöb
- `DETECTION_COOLDOWN = 2.0s` - Újabb detektálás várási idő

## 🛡️ Hibakezelés & Error Üzenetek

A rendszer automatikusan kezel hibákat és válaszol hangon keresztül:

| Hiba | TTS Üzenet | HTTP Kód | Log |
|------|-----------|----------|-----|
| **FORWARD_URL nem elérhető** | "Szolgáltatás átmenetileg nem elérhető!" | 503 | `[orchestrator] FORWARD_URL kapcsolódási hiba` |
| **STT feldolgozási hiba** | "Ismeretlen hibát kaptam! Próbálja meg később!" | 500 | `[orchestrator] STT hiba: ...` |
| **Config nincs beállítva** | "Rendszer nincs konfigurálva. Nyisson meg egy weboldalt a konfiguráláshoz." | 503 | `[orchestrator] FORWARD_URL nincs beállítva` |
| **Nincs audio felvétel** | (Csend, nincs TTS) | 400 | `[orchestrator] No audio detected` |
| **Érvénytelen audio formátum** | (Csend) | 400 | `[stt] Audio format error` |
| **TTS timeout** | (Csend) | 504 | `[orchestrator] TTS timeout` |

### Startup Logika

Az **orchestrator** vár a konfigurációra:
1. Induláskor ellenőrzi a `/app/config/forward_url.json` fájlt
2. Ha üres: vár 20 másodpercig (2 mp-es intervallumonként újrapróbál)
3. Ha 20 mp után sincs konfig: működik tovább, de figyelmeztet
4. Első wake eseménynél, ha nincs FORWARD_URL → hibaüzenet (503)

**Log példa:**
```
[orchestrator] Indulás...
[orchestrator] ⏳ FORWARD_URL nincs konfigurálva. Nyisson meg a config weboldalt.
[orchestrator]    (Várakozás... 0/20s)
[orchestrator] ✅ FORWARD_URL betöltve, indulás...
```

### Thread-Safety & Async Kezelés

**Kódminőség fejlesztések:**
- ✅ `ConfigManager`: Thread-safe config kezelés (RLock)
- ✅ Wake word threading: `asyncio.run_coroutine_threadsafe()` helyesen használva
- ✅ Audio processing: Válid error handling és timeout kezelés
- ✅ TTS/STT: HTTP timeout `30s`, proper exception handling

## 🖥️ Raspberry Pi 4 Optimalizáció

### Hardver követelmények
- **RAM:** 2GB minimum (4GB ajánlott kis modellek esetén)
- **Mikrofon:** USB vagy 3.5mm jack
- **Hangszóró:** 3.5mm, HDMI vagy USB
- **SD kártya:** 16GB minimum (32GB ajánlott)

### Teljesítmény (Pi 4 B, 2GB)

| Komponens | CPU | RAM | Válaszidő |
|-----------|-----|-----|-----------|
| Wake word (STT-based) | ~25% | ~200 MB | 0.5-1s |
| STT (base model) | ~80% (spike) | ~700 MB | 1-2s |
| Piper TTS | ~40% | ~150 MB | 0.5-1s |
| **Teljes workflow** | - | **~1.5 GB** | **3-5s** |

### Optimalizálási tippek

**1. Alacsony memória módok:**
```bash
export STT_MODEL_SIZE="tiny"   # ~400 MB RAM, gyorsabb de kevésbé pontos
```

**2. Wake word dedikált modell:**
- Tréningelhető OpenWakeWord/Mycroft Precise modell
- CPU csökkenés: 25% → ~5%
- Pontosabb detektálás

**3. Audio eszköz konfiguráció:**
```bash
# ALSA mixer beállítás (ha halk)
alsamixer

# Eszköz lista
arecord -l  # Mikrofon
aplay -l    # Hangszóró
```

## 🔧 Hibaelhárítás

### "No audio device found"
```bash
# Ellenőrizd az audio eszközöket
arecord -l
aplay -l

# Docker group jogosultság
sudo usermod -aG audio $USER
```

### STT túl lassú
```bash
export STT_MODEL_SIZE="tiny"
docker compose up
```

### Piper modellek nem töltődnek le
```bash
# Manuális letöltés
cd services/piper/
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/hu/hu_HU/berta/medium/hu_HU-berta-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/hu/hu_HU/berta/medium/hu_HU-berta-medium.onnx.json
```

### Config weboldal nem elérhető
```bash
# Ellenőrizd a port mappinget
docker compose ps
docker logs config

# HTTP timeout: 30s volt a probléma?
docker logs orchestrator | grep timeout
```

### STT/TTS timeout hibák
```bash
# Ellenőrizd a hálózati kapcsolatot
docker exec orchestrator ping stt
docker exec orchestrator ping piper

# Logs
docker logs stt
docker logs piper
```

### Szó felismerése nem működik
```bash
# Log: energia küszöb problémája?
docker logs wakeword | grep "energy"

# STT-alapú detektálás tesztelése (slow!):
docker logs wakeword | grep "STT check"

# Egyedi OpenWakeWord modell használata:
export WAKEWORD_MODEL_PATH="/path/to/model.oww"
docker compose up
```

## 📁 Fájlstruktúra

```
MicroPiSoundControl/
├── docker-compose.yml          # 5 szolgáltatás orchestration
├── README.md                   # Ez a fájl
└── services/
    ├── config/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   ├── app.py             # Config weboldal API
    │   └── index.html         # Config weboldal UI
    ├── wakeword/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app.py             # Wake word detektálás
    ├── stt/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app.py             # Whisper STT API
    ├── piper/
    │   ├── Dockerfile
    │   └── app.py             # Piper TTS API
    └── orchestrator/
        ├── Dockerfile
        ├── requirements.txt
        └── app.py             # Workflow koordináció
```

## 🎯 Következő Lépések & Fejlesztési Ötletek

1. **FORWARD_URL service implementálása:**
   - ChatGPT/Claude API wrapper
   - Home Assistant integráció
   - Rasa/Snips intent parser

2. **Wake word modell tréningelése:**
   - 30-60 "Mikrobi" minta gyűjtése
   - OpenWakeWord/Mycroft Precise tréning
   - Alacsonyabb CPU + jobb pontosság

3. **Multi-turn beszélgetés:**
   - Context tárolás session-ökben
   - Nem csak egyszeri kérdés-válasz

4. **Vizuális feedback:**
   - LED strip integráció (GPIO)
   - Állapot jelzés: éber/hallgat/gondolkodik/válaszol

5. **Offline LLM:**
   - Llama 3.2 1B modell helyben
   - Teljes offline működés

6. **MQTT/Home Assistant natív:**
   - Közvetlen MQTT protokoll
   - Node-RED integráció

---

**Projekt státusz:** Production-ready prototípus, működőképes architektúrával és Pi 4-re optimalizált konfigurációval.

**Licensz:** MIT (ha szeretnéd megosztani)  
**Szerző:** nagypal.marton  
**Dátum:** 2026. január

#### 3. **STT Service** (Port: 8002)
- Speech-to-Text: Whisper (faster-whisper optimalizált)
- REST API: `POST /transcribe` (multipart/form-data WAV/OGG)
- **Hibakezelés:** Érvénytelen audio formátum → 400, Transzkripció hiba → 500
- CPU optimalizált: int8 kvantálás, CPU threading limit
- Modell méret: tiny/base/small (default: `base` Pi 4-re)
- Nyelvmodell: **Fixed magyar** (nincs auto-detect → gyorsabb)

#### 4. **Piper TTS Service** (Port: 5000)
- Text-to-Speech: Piper neural TTS
- REST API: `POST /speak` (JSON: `{"text": "...", "language": "auto"}`)
- **Hibakezelés:** Missing voice → 500, Subprocess hiba → 500
- **Magyar:** hu_HU-berta-medium (női hang)
- **Angol:** en_US-lessac-medium (férfi hang)
- Automatikus nyelvfelismerés (magyar ékezetes karakterek alapján)
- **Resource:** `TemporaryDirectory()` cleanup (automatikus)

#### 5. **Orchestrator Service** (Port: 8003)
- Workflow koordinátor (szív)
- **Config kezelés:** Thread-safe `ConfigManager` (RLock protected)
- **Folyamat:**
  1. Wake esemény fogadása
  2. Mikrofon felvétel (VAD alapú csend detektálás, max 5 mp)
  3. STT hívás (transzkripció)
  4. FORWARD_URL hívás (szöveg feldolgozás)
  5. Piper TTS hívás (válasz szintézis)
  6. Hangszóró lejátszás
- **Startup:** Vár a FORWARD_URL konfigurációra (max 20 mp)
- **Error handling:** Standardizált HTTP status codes (400/500/503)
- **Timeout:** 30 másodperc minden HTTP request-hez

### Adatfolyam

```
[Mikrofon]
    ↓
┌─────────────────┐
│   WakeWord      │ "Mikrobi" detektálás
│  (folyamatos)   │
└─────────────────┘
    ↓ POST /wake
┌─────────────────┐
│  Orchestrator   │
│  1. Felvétel    │ ← [Mikrofon] (VAD, max 5s)
│  2. STT         │ ← POST /transcribe
│  3. Forward     │ → POST <FORWARD_URL>
│  4. TTS         │ ← POST /speak
│  5. Lejátszás   │ → [Hangszóró]
└─────────────────┘
```

## Megjegyzések & Kódminőség

**Architektúra javítások (v1.1):**
- ✅ Globális állapot eltávolítva: `ConfigManager` osztály thread-safe kezeléssel
- ✅ Magic constants kiválasztva: `HTTP_TIMEOUT`, `VAD_AGGRESSIVENESS`, stb.
- ✅ Asyncio/threading: `asyncio.run_coroutine_threadsafe()` helyes integrálás
- ✅ Error handling: Standardizált HTTP status codes (400/500/503)
- ✅ Audio validation: Format check + transzkripció error handling
- ✅ Resource cleanup: `tempfile.TemporaryDirectory()` context manager

**Mikrofon és hangkimenet eléréséhez:**
- Konténereknek hozzá kell férniük a `/dev/snd` eszközhöz
- Az `audio` csoporthoz kell tartozniuk

**Raspberry Pi 4 (2GB RAM) optimalizáció:**
- Alapértelmezett beállítások (STT: base, Piper: medium) jól működnek
- Alacsonyabb memóriahasználathoz: `STT_MODEL_SIZE=tiny` (400 MB)
- Wake word: STT-alapú detektálás működik, de CPU-igényes
  - **Javaslat:** Egyedi OpenWakeWord modell tanítása (~5% CPU vs 25% STT)

**Piper TTS:**
- Magyar és angol hangokat tartalmaz, automatikus nyelv-felismeréssel
- Magyar karakterek alapján felismer: áéíóöőúüű

**Wake word detektálás:**
- Ha nincs OpenWakeWord modell: STT-alapú (energia + gyors transzkripció)
- Működik de nagyobb CPU igény (25-40%)
- Éles használatra ajánlott: egyedi KWS modell tanítása

# Mikrobi - AI-Powered Smart Home System

Edge-cloud architecture for voice and text-based smart home control with LLM intelligence and Home Assistant integration.

## 🏗️ Architecture

Mikrobi is a distributed smart home system with two main layers:

**Edge Layer (Raspberry Pi 4):**
- Wake-word detection ("Mikrobi")
- Automatic Speech Recognition (ASR) - Hungarian and English
- Voice command processing
- Communication with assigned Home Assistant instance

**Central Layer (Kubernetes):**
- Backend services and user management
- Ollama LLM (Ministral 3 3B) for contextual intent processing
- Multi-user Home Assistant instances (one per user)
- Administration interface
- Monitoring and orchestration

**Key Design Principles:**
- One Raspberry Pi per user
- Edge devices communicate only via Home Assistant REST API
- No direct IoT device control from Raspberry Pi
- Request-level logical isolation for shared LLM

## 📋 System Components

### Edge Components
- **Wake-word Detection**: Continuous listening for "Mikrobi" trigger
- **ASR Service**: Speech-to-text conversion (Hungarian/English)
- **Edge Communicator**: REST API client for Home Assistant

### Central Components
- **User Management**: Registration, authentication, profile management
- **Home Assistant Instances**: Isolated per-user smart home control
- **LLM Service**: Ollama with Ministral 3 3B for contextual commands
- **Intent Processor**: Routes explicit commands directly, contextual to LLM
- **Admin UI**: System management and monitoring
- **User UI**: Login, registration, Home Assistant instance access

### Infrastructure
- **Docker**: Containerized components
- **Kubernetes**: Orchestration for central services
- **Terraform**: Infrastructure as Code for HA instances and services
- **Zabbix**: Comprehensive monitoring

## 🚀 Quick Start

### Prerequisites

**Edge Device:**
- Raspberry Pi 4 (2GB RAM minimum)
- Microphone
- Network connectivity

**Central Infrastructure:**
- Kubernetes cluster (1.28+)
- NVIDIA GPU for LLM inference
- 16GB+ RAM
- 100GB+ storage for models

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd HomeAssistantantWithLocalAIVoiceControll

# Setup central services
./scripts/setup-local.sh

# Deploy Home Assistant instance
./scripts/create-ha-instance.sh <username>
```

### Edge Device Setup

```bash
# On Raspberry Pi
./scripts/setup-edge.sh

# Configure user assignment
./scripts/configure-edge.sh --user=<username>
```

## 🎤 Voice Control

### Wake-word Activation
1. Say "Mikrobi" to activate
2. Wait for acknowledgment tone
3. Speak your command in Hungarian or English
4. System provides audio/text feedback

### Command Types

**Explicit Commands** (Direct to Home Assistant):
- "Kapcsold fel a lámpát" (Turn on the light)
- "Állítsd 22 fokra a termosztátot" (Set thermostat to 22°C)

**Contextual Commands** (Processed by LLM):
- "Sötét van a konyhában" (It's dark in the kitchen)
- "Fázom" (I'm cold)
- LLM interprets intent and suggests appropriate actions

## 💬 Text Control

Access the web interface to send text commands:
- Same intent processing as voice commands
- Full Home Assistant device control
- Automation creation with approval workflow

## 🔐 Security Features

- User authentication required
- Each user has isolated Home Assistant instance
- Security-critical operations require confirmation
- Voice and text data **not stored** (immediate deletion)
- Internet-accessible with proper authentication

## 🤖 LLM Intelligence

**Ministral 3 3B Model via Ollama:**
- Contextual command interpretation
- Access to full Home Assistant state
- Automation creation capabilities
- Logical request-level isolation

**Automation Workflow:**
1. LLM suggests automation based on command
2. User must approve before creation
3. Automation deployed to user's HA instance

## 📊 Monitoring

Zabbix monitors all system components:
- Kubernetes and Docker services
- Home Assistant API availability
- Ollama/LLM metrics and performance
- Raspberry Pi health (lightweight HTTP exporter)
- Custom alerts and dashboards

## 🔧 User Management

### Registration
- First name, last name, location, password
- Automatic Home Assistant instance creation
- Unique instance URL assigned

### Account Deletion
- Complete removal of user data
- Permanent deletion of associated HA instance

## 📈 Performance Targets

- Wake-word detection: < 500ms
- LLM response time: < 3 seconds
- System availability: 99%

## 🛠️ DevOps & Updates

**Automatic Updates:**
- Raspberry Pi OS and containers (automatic)

**Manual Updates:**
- Backend services (admin approval required)
- Kubernetes deployments

**Infrastructure:**
```bash
# Deploy infrastructure changes
cd terraform/environments/prod
terraform plan
terraform apply

# Update central services
./scripts/deploy-k8s.sh prod
```

## 📚 Documentation

- [Software Requirements Specification](mikrobi_okosotthon_rendszer_srs.md) - Complete system specification
- [Setup Guide](docs/SETUP.md) - Installation and configuration
- [Edge Device Guide](docs/EDGE_SETUP.md) - Raspberry Pi setup
- [Architecture Details](docs/ARCHITECTURE.md) - System design

## 🎯 Key Features

✅ Wake-word activated voice control  
✅ Multi-language support (Hungarian, English)  
✅ LLM-powered contextual understanding  
✅ One-to-one edge-to-user mapping  
✅ Isolated Home Assistant instances  
✅ Automation creation with approval  
✅ Text and voice control parity  
✅ Security confirmation for critical operations  
✅ Complete DevOps automation  
✅ Comprehensive monitoring  

## ⚙️ Project Structure

```
.
├── docker/                  # Docker configurations
│   ├── edge/               # Raspberry Pi services
│   ├── backend/            # Central services
│   └── home-assistant/     # HA templates
├── kubernetes/              # K8s manifests
│   ├── ollama/
│   ├── backend/
│   └── monitoring/
├── terraform/               # Infrastructure as Code
│   ├── ha-instance/        # HA provisioning
│   └── cluster/            # K8s setup
├── edge/                    # Raspberry Pi code
│   ├── wake-word/
│   ├── asr/
│   └── communicator/
├── backend/                 # Central services code
│   ├── user-service/
│   ├── intent-processor/
│   └── llm-gateway/
├── monitoring/              # Zabbix configs
├── scripts/                 # Automation scripts
└── docs/                    # Documentation
```

## 🚫 Limitations & Constraints

- One Raspberry Pi serves one user exclusively
- Edge devices do not control IoT devices directly
- GPU required for optimal LLM performance
- Internet connectivity required for operation

## 🆘 Support

For issues and questions:
- GitHub Issues: [Create an issue](../../issues)
- Documentation: [mikrobi_okosotthon_rendszer_srs.md](mikrobi_okosotthon_rendszer_srs.md)

## 📝 License

See [LICENSE](LICENSE) file for details.

---

**Mikrobi** - Your intelligent voice-controlled smart home assistant
