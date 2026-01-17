# PiSmartSpeaker - Home Assistant Voice Satellite

[![Edge Services CI](https://github.com/NagypalMarton/HomeAssistantantWithLocalAIVoiceControll/actions/workflows/edge-ci.yml/badge.svg)](https://github.com/NagypalMarton/HomeAssistantantWithLocalAIVoiceControll/actions/workflows/edge-ci.yml)
[![Edge ARM64 Raspberry Pi Testing](https://github.com/NagypalMarton/HomeAssistantantWithLocalAIVoiceControll/actions/workflows/edge-arm64-test.yml/badge.svg)](https://github.com/NagypalMarton/HomeAssistantantWithLocalAIVoiceControll/actions/workflows/edge-arm64-test.yml)
[![Edge AMD64 Integration Testing](https://github.com/NagypalMarton/HomeAssistantantWithLocalAIVoiceControll/actions/workflows/edge-amd64-test.yml/badge.svg)](https://github.com/NagypalMarton/HomeAssistantantWithLocalAIVoiceControll/actions/workflows/edge-amd64-test.yml)

🎙️ Raspberry Pi alapú hangvezérlésű satellite eszköz magyar nyelvű Home Assistant integrációval

## Áttekintés

Docker-alapú magyar nyelvű hangvezérelt rendszer Raspberry Pi 4-hez, amely Wyoming protokollt használ offline beszédfelismeréshez és szintézishez, majd kommunikál egy cloudban futó Home Assistant LLM-mel.

### Szolgáltatások

- **Wyoming-OpenWakeWord**: "Hey Jarvis" ébresztőszó felismerés (offline)
- **Wyoming-Whisper**: Magyar beszédfelismerés (ASR) - tiny-int8 modell (offline)
- **Wyoming-Piper**: Magyar hangszintézis (TTS) - hu_HU-imre-medium hang (offline)
- **Wyoming Satellite**: Koordinálja a szolgáltatásokat, mikrofon/hangszóró kezelés
- **Home Assistant Integration**: LLM-alapú parancsfelismerés és válaszgenerálás (cloud)

## 🚀 Gyors indítás

### 1. Előfeltételek

#### Hardver
- **Raspberry Pi 4 Model B** (minimum 2GB RAM)
- **USB mikrofon** (plughw:3,0 - 16kHz, mono, 16-bit PCM)
- **USB hangszóró** vagy aktív hangszórók (plughw:4,0 - 22050Hz, mono, 16-bit PCM)
- **16GB+ microSD kártya**
- **Stabil tápegység** (5V/3A)
- **Ethernet vagy WiFi** kapcsolat

#### Szoftver
- **Raspberry Pi OS** (64-bit ajánlott)
- **Docker Engine** és **Docker Compose** telepítve
- **Home Assistant** instance cloudban futó LLM-mel és Wyoming Integration-nel

### 2. Rendszer indítása

```bash
cd edge
docker compose up -d
```

**Első indulás ideje:** ~5-10 perc (modell letöltések)

**Automatikus újraindulás:** A Docker konténerek `restart: unless-stopped` politikával rendelkeznek, így áramkimaradás után automatikusan újraindulnak.

### 3. Home Assistant Wyoming Integration beállítása

1. **Home Assistant-ban:** Settings → Devices & Services → Add Integration → Wyoming Protocol
2. **Add meg a satellite adatait:**
   - **Host**: `<raspberry-pi-ip>`
   - **Port**: Wyoming Satellite által használt port
3. **Konfiguráld az LLM-et** a Home Assistant Conversation beállításokban

✅ **Kész!** A satellite automatikusan csatlakozik a Home Assistant-hoz

## 🎯 Használat

1. **Várd meg** amíg az összes konténer elindul és a modellek betöltődnek
2. **Mondj "Hey Jarvis"** - az ébresztőszót (max 500ms késleltetéssel észleli)
3. **Várd meg a hangjelzést** (opcionális)
4. **Mondj egy parancsot** magyarul, például:
   - "Kapcsold be a nappali lámpát"
   - "Milyen az időjárás?"
   - "Állítsd 22 fokra a termosztátot"
5. A rendszer **feldolgozza** (Whisper STT → Home Assistant LLM → Piper TTS)
6. A válasz **elhangzik** magyar férfi hanggal (Imre)
7. **Automatikus visszatérés** az ébresztőszó figyelés állapotába

### Teljesítmény célok (SRS követelmények)
- **Ébresztőszó felismerés**: max 500ms késleltetés
- **Beszédfelismerés**: valós idejű (RTF < 0.5)
- **TTS szintézis**: max 1s késleltetés
- **Teljes interakció**: < 5s (HA válaszidő nélkül)
- **Beszédrögzítés vége**: 2 másodperc csend után automatikusan

### Hibakezelés
- **Home Assistant nem elérhető**: *"A Home Assistant jelenleg nem elérhető."* üzenet
- **Időtúllépés** (5 másodperc): ugyanaz a hibaüzenet
- **Automatikus helyreállás**: hibaüzenet után visszatérés idle állapotba

#### HA elérhetetlenség riasztás (helyi Piper TTS)

Ha szeretnéd, hogy a satellite helyben kimondja: *"HA nem érhető el!"* amikor a Home Assistant nem elérhető, futtasd az `ha_healthwatch.sh` figyelő scriptet. Ez a Piper TTS-t használja és a hangot a Wyoming Satellite-on keresztül játssza le.

Lépések:

```bash
cd edge
# egyszeri: osztott cache könyvtár létrehozva és compose-ban felmountolva
# futtasd a stack-et
docker compose up -d

# állítsd be a HA URL-t (példa)
export HA_URL="http://homeassistant.local:8123"

# futtasd a figyelőt (15s-enként ellenőriz, 60s cooldown az ismételt riasztásra)
chmod +x ha_healthwatch.sh
./ha_healthwatch.sh
```

Megjegyzések:
- A script a `wyoming-piper` konténerben generál WAV fájlt a `tts-cache` megosztott könyvtárba, majd a `wyoming-satellite` konténer játsza le azt.
- A mikrofon/hangszóró beállításokhoz igazítva a lejátszás `aplay`-t használja (`plughw:4,0`). Ha az eszköz ID eltér, frissítsd a `docker-compose.yml`-t és a scriptet.
- Testreszabás: `ALERT_TEXT="HA nem érhető el!"`, `CHECK_INTERVAL`, `ALERT_COOLDOWN` környezeti változókkal.

## 📐 Architektúra

### Rendszer komponensek

```
┌─────────────────────────────────────────────────────────┐
│                   Wyoming Satellite                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Mikrofon    │  │  Hangszóró   │  │     VAD      │  │
│  │ (plughw:3,0) │  │ (plughw:4,0) │  │   (Silero)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────┬────────────┬────────────┬─────────────────┘
              │            │            │
         ┌────▼────┐  ┌────▼────┐  ┌───▼─────┐
         │OpenWake │  │ Whisper │  │  Piper  │
         │  Word   │  │  (ASR)  │  │  (TTS)  │
         │hey_jarvis│ │tiny-int8│  │hu-imre │
         └─────────┘  └─────────┘  └─────────┘
                           │            ▲
                           │            │
                      ┌────▼────────────┴─────┐
                      │   Home Assistant      │
                      │   (Cloud + LLM)       │
                      └───────────────────────┘
```

### Működési folyamat (State Machine)

1. **Idle állapot**: OpenWakeWord folyamatosan figyeli a "Hey Jarvis" ébresztőszót
2. **Wake**: Ébresztőszó észlelése (max 500ms) → Satellite aktiválás
3. **Listen**: VAD alapján hangrögzítés, amíg a felhasználó beszél (2s csend után vége)
4. **Transcribe**: Whisper tiny-int8 offline átalakítja szöveggé a hangot
5. **Process**: Felismert szöveg elküldése HA LLM-nek Wyoming protokollon keresztül
6. **Respond**: HA LLM válasz fogadása (5s timeout)
7. **Speak**: Piper TTS offline lejátssza a választ magyar Imre hanggal
8. **Return to Idle**: Visszatérés az 1. lépéshez (automatikus)

**Hibakezelés állapot**: Timeout vagy kapcsolódási hiba esetén hibaüzenet lejátszása → Return to Idle

### Szolgáltatások (Wyoming Protocol)

#### 1. **Wyoming-OpenWakeWord** (TCP: 10400)
- **Model**: `hey_jarvis.tflite` (egyedi magyar ébresztőszó)
- **Működés**: Offline, folyamatos audio stream figyelés
- **Threshold**: Beállítható érzékenység
- **Teljesítmény**: <500ms késleltetés, max 1 hamis pozitív/óra

#### 2. **Wyoming-Whisper STT** (TCP: 10300)
- **Backend**: faster-whisper (optimalizált C++ implementáció)
- **Model**: `tiny-int8` (39M params, ~75MB, quantizált)
- **Nyelv**: Magyar (hu)
- **Teljesítmény**: RTF < 0.5 (valós idejű)
- **Eszköz**: CPU only (Raspberry Pi 4)

#### 3. **Wyoming-Piper TTS** (TCP: 10200)
- **Model**: `hu_HU-imre-medium` (magyar férfi hang)
- **Format**: ONNX
- **Sample rate**: 22050 Hz
- **Minőség**: Közepes (természetes, tisztán érthető)
- **Működés**: Offline szintézis
- **Teljesítmény**: <1s késleltetés

#### 4. **Wyoming Satellite**
- **Mikrofon**: USB (plughw:3,0), 16kHz, mono, 16-bit PCM
- **Hangszóró**: USB (plughw:4,0), 22050Hz, mono, 16-bit PCM
- **VAD**: Voice Activity Detection (Silero)
- **Koordináció**: Wake Word → STT → HA → TTS pipeline
- **Timeout**: 5s HA kommunikációra

### Adatfolyam és protokoll

```
Mikrofon (16kHz) → Wyoming-OpenWakeWord (Hey Jarvis detektálás)
                         ↓ (wake event, <500ms)
                    Wyoming Satellite (audio recording + VAD)
                         ↓ (audio stream, 2s csend után vége)
                    Wyoming-Whisper (offline STT, RTF<0.5)
                         ↓ (magyar szöveg)
                    Home Assistant LLM (cloud, Wyoming protocol)
                         ↓ (válasz szöveg, 5s timeout)
                    Wyoming-Piper (offline TTS, <1s)
                         ↓ (audio stream, 22050Hz)
                    Hangszóró
                         ↓
                    Return to Idle (OpenWakeWord figyelés)
```

**Adatvédelem és biztonság:**
- ❌ **Nem kerül fel a cloud-ba**: Eredeti hangfelvétel (mikrofon audio)
- ✅ **Fel kerül a cloud-ba**: Felismert szöveg (Whisper output → HA LLM)
- ✅ **Titkosított kapcsolat**: HTTPS/WSS a Home Assistant felé
- ✅ **Offline feldolgozás**: Wake Word, STT, TTS helyben fut

## 🔧 Home Assistant beállítás

A rendszer a **Wyoming Integration** és **Conversation API**-t használja.

### 1. Wyoming Integration telepítése

Home Assistant-ban:
```
Settings → Devices & Services → Add Integration → Wyoming Protocol
```

Konfiguráció:
- **Host**: Raspberry Pi IP címe
- **Port**: Wyoming Satellite port
- **SSL**: Nem (helyi hálózat)

### 2. LLM konfiguráció a Conversation API-hoz

A Home Assistant támogatja különböző LLM-eket, amelyek automatikusan integrálódnak:

#### OpenAI ChatGPT
```yaml
# configuration.yaml
openai_conversation:
  api_key: !secret openai_api_key
```

#### Google Generative AI
```yaml
# configuration.yaml
google_generative_ai_conversation:
  api_key: !secret google_api_key
```

#### Ollama (helyi LLM)
```yaml
# configuration.yaml
ollama:
  host: http://192.168.1.100:11434
  model: llama2
```

### 3. Home Assistant natív intent kezelés

Alapértelmezett intentek magyarul is működnek:
- Eszköz be/kikapcsolás: *"Kapcsold be a nappali lámpát"*
- Fény szabályozás: *"Állítsd 50%-ra a hálószoba lámpáját"*
- Klíma vezérlés: *"Állítsd 22 fokra a termosztátot"*
- Időjárás lekérdezés: *"Milyen az időjárás?"*

### 4. Custom intentek (opcionális)

`configuration.yaml`:
```yaml
intent_script:
  CustomLightScene:
    speech:
      text: "Bekapcsoltam a {{ scene }} világítást"
    action:
      - service: scene.turn_on
        target:
          entity_id: "scene.{{ scene }}"
```

**Fontos**: A satellite **csak az LLM válaszát játssza le**, egyéb feldolgozás nélkül. A beszélgetési logikát a Home Assistant LLM kezeli.

## 🐛 Hibaelhárítás

### 1. Ébresztőszó ("Hey Jarvis") nem érzékelhető

```bash
# Ellenőrizd a mikrofon működését
docker exec -it wyoming-openwakeword python -c "import sounddevice as sd; print(sd.query_devices())"

# Mikrofon teszt (hang felvétel)
arecord -D plughw:3,0 -f S16_LE -r 16000 -c 1 -d 5 test.wav

# Logok ellenőrzése
docker logs wyoming-openwakeword -f
```

**Megoldások:**
- Csökkentsd a threshold értéket (érzékenyebb)
- Ellenőrizd, hogy a mikrofon device helyes-e (plughw:3,0)
- Beszélj tisztábban és közelebb a mikrofonhoz
- **Hamis pozitív arány**: max 1/óra az SRS követelmény szerint

### 2. "A Home Assistant jelenleg nem elérhető" hibaüzenet

Ez a hibaüzenet akkor hangzik el, amikor:
- A Home Assistant nem válaszol 5 másodpercen belül (timeout)
- Hálózati kapcsolat megszakadt
- Wyoming Integration nincs konfigurálva

```bash
# Ellenőrizd a hálózati kapcsolatot
ping <home-assistant-ip>

# Ellenőrizd a Wyoming Integration-t HA-ban
# Settings → Devices & Services → Wyoming Protocol

# Satellite logok
docker logs wyoming-satellite -f
```

**Megoldás:**
- Konfiguráld a Wyoming Integration-t Home Assistant-ban
- Ellenőrizd a tűzfal beállításokat
- Bizonyosodj meg, hogy a HA elérhető az internetről (cloud)

### 3. STT nem működik / rossz transzkripció

```bash
# Whisper logok ellenőrzése
docker logs wyoming-whisper -f

# Nagyobb model használata (lassabb, de pontosabb)
# docker-compose.yml-ben változtasd meg:
# WHISPER_MODEL=base
```

**Megjegyzés:** A `tiny-int8` modell optimalizált a gyorsaságra (RTF < 0.5), de időnként kevésbé pontos. Hosszabb szövegeknél vagy zajosabb környezetben `base` vagy `small` modellt érdemes használni.

### 4. TTS hang minősége rossz

```bash
# Piper logok
docker logs wyoming-piper -f

# Ellenőrizd, hogy az Imre modell betöltődött-e
docker exec wyoming-piper ls /data/
```

A `hu_HU-imre-medium` modell a legjobb egyensúly a sebesség és a minőség között. Ha jobb minőséget szeretnél, próbáld a `hu_HU-imre-high` modellt (lassabb).

### 5. Rendszer nem indul újra áramkimaradás után

```bash
# Ellenőrizd a restart policy-t
docker ps -a

# Minden konténernek "unless-stopped" restart policy-nek kell lennie
docker inspect wyoming-satellite | grep -A 5 RestartPolicy
```

**Megoldás:** `docker-compose.yml`-ben minden service-nél:
```yaml
restart: unless-stopped
```

### 6. Hangszóró nem játszik le hangot

```bash
# Hangszóró teszt
aplay -D plughw:4,0 -f S16_LE -r 22050 -c 1 /usr/share/sounds/alsa/Front_Center.wav

# Volume ellenőrzése
amixer scontrols
amixer set Master 80%
```

### 7. Logok megtekintése

```bash
# Összes szolgáltatás
docker compose logs -f

# Specifikus szolgáltatás
docker compose logs -f wyoming-satellite
docker compose logs -f wyoming-whisper
docker compose logs -f wyoming-piper
docker compose logs -f wyoming-openwakeword
```

## 🔄 Wyoming Protokoll

A rendszer a [Wyoming protokollt](https://github.com/rhasspy/wyoming) használja, amely:
- **Egységes interfész** különböző voice assistant szolgáltatásokhoz
- **TCP socket alapú** kommunikáció és event streaming
- **Event-based** architektúra (wake, audio-start, audio-chunk, audio-stop, transcript, synthesize, stb.)
- **Home Assistant natív** támogatás (Wyoming Integration)
- **Offline-first**: Helyi feldolgozás támogatása (STT, TTS, Wake Word)

### Service portok

| Service | Port | Protokoll | Funkció |
|---------|------|-----------|---------|
| Wyoming-OpenWakeWord | 10400 | TCP (Wyoming) | Ébresztőszó felismerés |
| Wyoming-Whisper (STT) | 10300 | TCP (Wyoming) | Beszédfelismerés |
| Wyoming-Piper (TTS) | 10200 | TCP (Wyoming) | Hangszintézis |
| Wyoming Satellite | - | - | Koordinátor (mikrofon/hangszóró) |

### Wyoming Events példa

```
1. Client → OpenWakeWord: Audio stream (16kHz)
2. OpenWakeWord → Client: Detection event ("Hey Jarvis")
3. Client → Whisper: Audio stream (beszéd)
4. Whisper → Client: Transcript event ("kapcsold be a lámpát")
5. Client → HA LLM: Text request (Wyoming protocol)
6. HA LLM → Client: Response ("Bekapcsoltam a nappali lámpáját")
7. Client → Piper: Synthesize event (szöveg)
8. Piper → Client: Audio stream (22050Hz, TTS output)
```

## 📦 Szolgáltatások részletei

### OpenWakeWord (Port: 10400)
- **Model**: `hey_jarvis.tflite` (egyedi magyar wake word)
- **Input**: 16kHz, mono, 16-bit PCM audio stream
- **Output**: Detection event (wake word detected)
- **Threshold**: 0.5 (alapértelmezett, beállítható)
- **Latency**: <500ms (SRS követelmény)
- **False positive rate**: max 1/óra

### Whisper STT (Port: 10300)
- **Backend**: faster-whisper (ctranslate2 optimalizáció)
- **Model**: `tiny-int8` (39M params, ~75MB, INT8 quantized)
- **Nyelv**: Magyar (hu)
- **Input**: 16kHz audio stream (VAD által szegmentált)
- **Output**: Transcript text (magyar szöveg)
- **RTF**: <0.5 (valós idejű feldolgozás)
- **Beam size**: 5 (alapértelmezett)
- **VAD**: Silero VAD (2s csend után vége)

### Piper TTS (Port: 10200)
- **Model**: `hu_HU-imre-medium` (magyar férfi hang)
- **Format**: ONNX (optimalizált inferencia)
- **Input**: Magyar szöveg (HA LLM válasz)
- **Output**: 22050Hz, mono, 16-bit PCM audio stream
- **Quality**: Medium (természetes, tisztán érthető)
- **Latency**: <1s (SRS követelmény)
- **Speaker**: Imre (férfi, közép-magyar akcentus)

### Wyoming Satellite
- **Mikrofon**: USB device (plughw:3,0)
  - Format: 16kHz, mono, 16-bit PCM
  - Buffer: Konfigurálható
- **Hangszóró**: USB device (plughw:4,0)
  - Format: 22050Hz, mono, 16-bit PCM
  - Volume: ALSA mixer vezérlés
- **VAD**: Voice Activity Detection (beszéd szegmentálás)
  - Engine: Silero VAD
  - Silence timeout: 2s (befejeződik a felvétel)
- **Pipeline**: Wake → Record → STT → HA → TTS → Play → Idle
- **Timeout**: 5s (HA kommunikáció)
- **Error handling**: "A Home Assistant jelenleg nem elérhető"
- **Restart policy**: `unless-stopped` (automatikus újraindulás)

## 📁 Fájlstruktúra

```
edge/
├── docker-compose.yml           # Docker szolgáltatások definíciója
├── README.md                    # Ez a dokumentáció
├── SRS.md                       # Software Requirements Specification
├── test-dependencies.sh         # Függőségek tesztelése
├── test-health.sh               # Healthcheck script
├── oww-data/                    # OpenWakeWord adatok (bind mount)
│   ├── alexa.json              # Alexa model metadata (nem használt)
│   ├── alexa.tflite            # Alexa model (nem használt)
│   ├── hey_jarvis.json         # Hey Jarvis model metadata ✅
│   └── hey_jarvis.tflite       # Hey Jarvis TFLite model ✅
├── oww-models/                  # OpenWakeWord modellek (bind mount)
│   ├── alexa.json
│   ├── alexa.tflite
│   ├── hey_jarvis.json         # Aktív model ✅
│   └── hey_jarvis.tflite       # Aktív model ✅
├── piper-data/                  # Piper TTS adatok (bind mount)
│   ├── hu_HU-imre-medium.onnx       # TTS model ✅
│   └── hu_HU-imre-medium.onnx.json  # TTS config ✅
└── whisper-data/                # Whisper STT adatok (cache volume)
    └── models--rhasspy--faster-whisper-tiny-int8/
        ├── blobs/               # Model fájlok
        ├── refs/                # Git referenciák
        └── snapshots/           # Model snapshot
            └── 5b6382e0f4ac867ce9ff24aaa249400a7c6c73d9/
                ├── config.json          # Whisper config
                └── vocabulary.txt       # Magyar szókincs
```

### Konfiguráció és volumék

- **oww-data/** és **oww-models/**: OpenWakeWord modellek és metaadatok
  - `hey_jarvis.tflite` - Az aktív ébresztőszó model
- **piper-data/**: Piper TTS model és konfiguráció
  - `hu_HU-imre-medium.onnx` - Magyar férfi hang (Imre)
- **whisper-data/**: Whisper STT model cache
  - Automatikusan letöltődik első induláskor (Hugging Face)
  - `tiny-int8` - Gyors és hatékony magyar beszédfelismerés

**Megjegyzés:** A modellek a kötetek (volumes) segítségével perzisztensek maradnak container újraindítás vagy update esetén is.

## 🚀 Fejlesztési ötletek

### Rövid távú fejlesztések
- [ ] **Streaming STT**: Valós idejű transzkripció Wyoming streaming API-val
- [ ] **Konfigurálható timeout**: 5s helyett felhasználó által beállítható
- [ ] **LED visszajelzés**: Vizuális jelzés GPIO-n keresztül (Wake, Listen, Think, Speak státuszok)
- [ ] **Hangjelzés customizálás**: Egyedi hangok Wake és hibaállapotokhoz

### Középtávú fejlesztések
- [ ] **Multi-room support**: Több Raspberry Pi különböző szobákban, központi koordinációval
- [ ] **Context awareness**: Dialógus történet tárolása és használata
- [ ] **Offline fallback intentek**: Alapvető parancsok (pl. timer) offline feldolgozása
- [ ] **Whisper model váltás**: Automatikus váltás `base` vagy `small` modellre összetett beszéd esetén
- [ ] **Home Assistant state tracking**: Lokális cache az eszköz állapotokról

### Hosszú távú fejlesztések
- [ ] **Wake word testreszabás**: Saját magyar wake word tanítása
- [ ] **Több nyelv támogatása**: Automatikus nyelvfelismerés és váltás
- [ ] **Lokális LLM integráció**: Alapvető parancsok feldolgozása Raspberry Pi-n (pl. Ollama)
- [ ] **Voice biometrics**: Felhasználó azonosítása hang alapján

### Teljesítmény optimalizálás
- [ ] **Model quantization**: További optimalizálás (pl. ONNX Runtime)
- [ ] **GPU acceleration**: Raspberry Pi 5 Neural Engine használata
- [ ] **Audio pipeline optimalizálás**: Csökkentett buffer latency
- [ ] **Parallel processing**: VAD és Wake Word párhuzamos futtatása

## 📊 Teljesítmény követelmények (SRS)

### Funkcionális követelmények teljesítése
✅ **REQ-F-001-003**: Ébresztőszó felismerés ("Hey Jarvis") offline  
✅ **REQ-F-004-007**: Magyar beszédfelismerés offline (Whisper tiny-int8, VAD)  
✅ **REQ-F-008-011**: Home Assistant LLM kommunikáció (Wyoming)  
✅ **REQ-F-012-014**: Magyar TTS offline (Piper Imre)  
✅ **REQ-F-015-017**: Hibakezelés (timeout, kapcsolódási hiba)

### Nem-funkcionális követelmények célértékei
- ⚡ **REQ-NF-001**: Ébresztőszó felismerés <500ms
- ⚡ **REQ-NF-002**: Beszédfelismerés RTF <0.5
- ⚡ **REQ-NF-003**: Teljes interakció <5s (HA nélkül)
- ⚡ **REQ-NF-004**: TTS szintézis <1s
- 🛡️ **REQ-NF-005**: 99% uptime (helyi hálózat)
- 🔄 **REQ-NF-006-007**: Automatikus újraindulás (`unless-stopped`)
- 🔒 **REQ-NF-011-013**: Offline feldolgozás, HTTPS/WSS kapcsolat
- 🐳 **REQ-NF-014-016**: Docker konténerek, külön volumék, Docker logs

## 🔗 Kapcsolódó dokumentumok

- **[SRS.md](SRS.md)**: Részletes szoftverkövetelmény specifikáció
- **[docker-compose.yml](docker-compose.yml)**: Docker szolgáltatások konfigurációja
- **[Wyoming Protocol Documentation](https://github.com/rhasspy/wyoming)**: Hivatalos Wyoming dokumentáció
- **[Home Assistant Wyoming Integration](https://www.home-assistant.io/integrations/wyoming/)**: HA integráció útmutató

## 📄 Licenc

MIT

---

**Verzió:** 1.0  
**Utolsó frissítés:** 2026. január 17.  
**Szerző:** Nagypal Márton
