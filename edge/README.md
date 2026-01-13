# MicroPiSoundControl

[![Edge Services CI](https://github.com/NagypalMarton/HomeAssistantantWithLocalAIVoiceControll/actions/workflows/edge-ci.yml/badge.svg)](https://github.com/NagypalMarton/HomeAssistantantWithLocalAIVoiceControll/actions/workflows/edge-ci.yml)
[![Edge ARM64 Raspberry Pi Testing](https://github.com/NagypalMarton/HomeAssistantantWithLocalAIVoiceControll/actions/workflows/edge-arm64-test.yml/badge.svg)](https://github.com/NagypalMarton/HomeAssistantantWithLocalAIVoiceControll/actions/workflows/edge-arm64-test.yml)
[![Edge AMD64 Integration Testing](https://github.com/NagypalMarton/HomeAssistantantWithLocalAIVoiceControll/actions/workflows/edge-amd64-test.yml/badge.svg)](https://github.com/NagypalMarton/HomeAssistantantWithLocalAIVoiceControll/actions/workflows/edge-amd64-test.yml)
🎙️ Wyoming Protocol alapú hangvezérelt asszisztens rendszer Home Assistant integrációval

## Áttekintés

Docker-alapú hangvezérelt rendszer Raspberry Pi-hez, amely Wyoming protokollt használ a szolgáltatások közötti kommunikációra és Home Assistant Conversation API-val integrálódik.

### Szolgáltatások

- **Wyoming-OpenWakeWord**: "Alexa" ébresztőszó detektálás
- **Wyoming-Whisper**: Speech-to-Text (STT) magyar nyelv támogatással (tiny model)
- **Wyoming-Piper**: Text-to-Speech (TTS) magyar Anna hanggal
- **Config Web**: Home Assistant konfiguráció (TOKEN + URL) webes felületen
- **Orchestrator**: Koordinálja a szolgáltatásokat és kommunikál a Home Assistant-tal

## 🚀 Gyors indítás

### 1. Előfeltételek

- Docker és Docker Compose telepítve
- Raspberry Pi vagy Linux számítógép mikrofonnal és hangszóróval
- **Home Assistant instance** futó API hozzáféréssel

### 2. Rendszer indítása

```bash
cd /home/nagypal.marton/Documents/MicroPiSoundControl
docker compose build
docker compose up
```

**Első indulás ideje:** ~5-10 perc (modell letöltések)

### 3. Home Assistant Konfigurálása (Webfelületen)

1. **Nyisd meg a konfigurációs weboldalt:**
   ```
   http://localhost:8000
   ```
   vagy Raspberry Pi IP-jével:
   ```
   http://<raspberry-pi-ip>:8000
   ```

2. **Szerezd meg a Home Assistant Long-Lived Access Token-t:**
   - Nyisd meg Home Assistant-ot
   - Kattints a profil ikonra (bal alsó sarokban)
   - Görgess le a "Long-Lived Access Tokens" részhez
   - Kattints "Create Token" gombra
   - Add neki egy nevet (pl. "MicroPi Voice")
   - **Másold ki a tokent** (csak egyszer jelenik meg!)

3. **Töltsd ki a konfigurációs oldalt:**
   - **Home Assistant URL**: `http://192.168.1.100:8123` (cseréld ki a tényleges IP-re/doménre)
   - **Token**: Az 2. lépésből másolt token
   - Kattints "Konfiguráció Mentése" gombra

✅ **Kész!** Az orchestrator automatikusan csatlakozik a Home Assistant-hoz

## 🎯 Használat

1. **Várd meg** amíg az összes konténer elindul
2. **Mondj "Alexa"** - az ébresztőszót
3. **Várd meg a hangjelzést** (ha van)
4. **Mondj egy parancsot** magyarul, pl.:
   - "Kapcsold be a nappali lámpát"
   - "Milyen az időjárás?"
   - "Állítsd 22 fokra a termosztátot"
5. A rendszer **feldolgozza** és **válaszol** magyarul

## 📐 Architektúra

### Szolgáltatások (Wyoming Protocol)

#### 1. **Wyoming-OpenWakeWord** (TCP: 10400)
- Ébresztőszó detektálás ("Alexa")
- Wyoming protokoll audio stream kezelés
- Beállítható érzékenység (threshold)

#### 2. **Wyoming-Whisper STT** (TCP: 10300)
- Speech-to-Text magyar nyelv támogatással
- Faster-Whisper backend (optimalizált)
- tiny model (gyors, alacsony erőforrásigény)

#### 3. **Wyoming-Piper TTS** (TCP: 10200)
- Text-to-Speech magyar Anna hanggal
- Natív Wyoming protokoll
- Valós idejű audio streaming

#### 4. **Orchestrator**
- Koordinálja a Wyoming szolgáltatásokat
- Mikrofon kezelés (felvétel ébresztőszó után)
- Home Assistant Conversation API integráció
- Audio lejátszás

### Adatfolyam

```
Mikrofon → Wyoming-OpenWakeWord (Alexa detektálás)
              ↓ (wake detected)
         Orchestrator (felvétel)
              ↓ (audio)
         Wyoming-Whisper (STT)
              ↓ (magyar szöveg)
         Home Assistant Conversation API
              ↓ (válasz szöveg)
         Wyoming-Piper (TTS)
              ↓ (audio)
         Hangszóró
```

## 🔧 Home Assistant beállítás

A rendszer a **Conversation API**-t használja, amely támogatja:

### 1. Natív Home Assistant intent kezelés
Alapértelmezetten elérhető intentek (magyar nyelven is):
- Eszköz be/kikapcsolás
- Fény szabályozás
- Klíma vezérlés
- stb.

### 2. Custom intentek (opcionális)

`configuration.yaml`:
```yaml
intent_script:
  TurnOnLight:
    speech:
      text: "Bekapcsoltam a {{ state_attr(area, 'friendly_name') }} lámpáját"
    action:
      - service: light.turn_on
        target:
          area_id: "{{ area }}"
```

### 3. AI asszisztensek (opcionális)

Home Assistant támogatja:
- Google Generative AI
- OpenAI ChatGPT
- Local LLMs (Ollama, etc.)

Ezek automatikusan integrálódnak a Conversation API-val.

## 🐛 Hibaelhárítás

### 1. Konfiguráció weboldal nem érhető el
```bash
# Ellenőrizd, hogy a config konténer fut-e
docker ps | grep config

# Logok megtekintése
docker logs config
```

### 2. "Rendszer nincs konfigurálva" hibaüzenet
- Nyisd meg `http://localhost:8000`
- Töltsd ki a Home Assistant URL-t és tokent
- Kattints "Konfiguráció Mentése" gombra

### 3. "Nem tudok csatlakozni a Home Assistant-hoz"
```bash
# Ellenőrizd a Home Assistant URL-t
curl http://192.168.1.100:8123/api/

# Ellenőrizd a tokent (helyesírás, karakterek)
# A tokennek legalább 20 karakter hosszúnak kell lennie
```

### 4. Wake word nem érzékelhető
```bash
# Ellenőrizd a mikrofon működését
docker exec -it orchestrator python -c "import sounddevice as sd; print(sd.query_devices())"

# Csökkentsd a threshold értéket az .env-ben:
THRESHOLD=0.3

# Újraindítás
docker compose restart wakeword
```

### 5. STT nem működik / rossz transzkripció
```bash
# Nagyobb model használata (lassabb, de pontosabb)
# docker-compose.yml-ben:
WHISPER_MODEL=base

# Beam size növelése
BEAM_SIZE=3

docker compose restart stt
```

### 6. Logok megtekintése
```bash
# Összes szolgáltatás
docker compose logs -f

# Specifikus szolgáltatás
docker compose logs -f orchestrator
docker compose logs -f stt
docker compose logs -f piper
docker compose logs -f wakeword
docker compose logs -f config
```

## 🔄 Wyoming Protokoll

A rendszer a [Wyoming protokollt](https://github.com/rhasspy/wyoming) használja, amely:
- **Egységes interfész** különböző voice assistant szolgáltatásokhoz
- **TCP socket alapú** kommunikáció
- **Event-based** architektúra
- **Home Assistant natív** támogatás

### Service portok

| Service | Port | Protokoll |
|---------|------|-----------|
| Config Web | 8000 | HTTP |
| Wyoming-Whisper (STT) | 10300 | TCP |
| Wyoming-Piper (TTS) | 10200 | TCP |
| Wyoming-OpenWakeWord | 10400 | TCP |

## 📦 Szolgáltatások részletei

### Config Web (Port: 8000)
- Flask webserver
- Home Assistant URL és TOKEN konfigurálása
- Webes UI magyar nyelvű
- Konfigurációs fájl: `/app/config/ha_config.json`

### Whisper (STT)
- **Backend**: faster-whisper
- **Model**: tiny (39M params, ~75MB)
- **Nyelv**: Magyar (hu)
- **Optimization**: int8 quantization
- **Eszköz**: CPU only

### Piper (TTS)
- **Model**: hu_HU-anna-medium
- **Format**: ONNX
- **Sample rate**: 22050 Hz
- **Minőség**: Közepes (gyors + jó minőség egyensúly)

### OpenWakeWord
- **Model**: alexa (beépített)
- **Sample rate**: 16000 Hz
- **Threshold**: 0.5 (alapértelmezett)

## 📁 Fájlstruktúra

```
MicroPiSoundControl/
├── docker-compose.yml
├── README.md
└── services/
    ├── config/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app.py             # Flask konfiguráció app
    ├── wakeword/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app.py
    ├── stt/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app.py
    ├── piper/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app.py
    └── orchestrator/
        ├── Dockerfile
        ├── requirements.txt
        └── app.py
```

## 🚀 Fejlesztési ötletek

- [ ] **Multi-room support**: Több Raspberry Pi különböző szobákban
- [ ] **Wake word testreszabás**: Magyar "Mikrobi" vagy saját modell
- [ ] **Streaming STT**: Valós idejű transzkripció Wyoming streaming API-val
- [ ] **Voice activity detection**: Automatikus felvétel vége detektálás
- [ ] **Context awareness**: Dialógus történet tárolás
- [ ] **Több nyelv**: Automatikus nyelvfelismerés és váltás

## 📄 Licenc

MIT
- `HTTP_TIMEOUT = 30s` - STT, TTS, Forward request timeout

## 🚀 Fejlesztési ötletek

- [ ] **Multi-room support**: Több Raspberry Pi különböző szobákban
- [ ] **Wake word testreszabás**: Magyar "Mikrobi" vagy saját modell
- [ ] **Streaming STT**: Valós idejű transzkripció Wyoming streaming API-val
- [ ] **Voice activity detection**: Automatikus felvétel vége detektálás
- [ ] **Context awareness**: Dialógus történet tárolás
- [ ] **Több nyelv**: Automatikus nyelvfelismerés és váltás

## 📄 Licenc

MIT
