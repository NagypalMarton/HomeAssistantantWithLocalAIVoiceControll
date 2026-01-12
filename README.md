# MicroPiSoundControl

🎙️ Wyoming Protocol alapú hangvezérelt asszisztens rendszer Home Assistant integrációval

## Áttekintés

Docker-alapú hangvezérelt rendszer Raspberry Pi-hez, amely Wyoming protokollt használ a szolgáltatások közötti kommunikációra és Home Assistant Conversation API-val integrálódik.

### Szolgáltatások

- **Wyoming-OpenWakeWord**: "Alexa" ébresztőszó detektálás
- **Wyoming-Whisper**: Speech-to-Text (STT) magyar nyelv támogatással (tiny model)
- **Wyoming-Piper**: Text-to-Speech (TTS) magyar Anna hanggal
- **Orchestrator**: Koordinálja a szolgáltatásokat és kommunikál a Home Assistant-tal

## 🚀 Gyors indítás

### 1. Előfeltételek

- Docker és Docker Compose telepítve
- Raspberry Pi vagy Linux számítógép mikrofonnal és hangszóróval
- **Home Assistant instance** futó API hozzáféréssel
- Home Assistant **Long-Lived Access Token**

### 2. Home Assistant Token megszerzése

1. Nyisd meg Home Assistant-ot
2. Kattints a profil ikonra (bal alsó sarokban)
3. Görgess le a "Long-Lived Access Tokens" részhez
4. Kattints "Create Token" gombra
5. Add neki egy nevet (pl. "MicroPi Voice")
6. Másold ki a tokent (csak egyszer jelenik meg!)

### 3. Környezeti változók beállítása

Hozz létre egy `.env` fájlt a projekt gyökérkönyvtárában:

```bash
# Home Assistant konfiguráció
HA_URL=http://192.168.1.100:8123
HA_TOKEN=your_long_lived_access_token_here

# Opcionális beállítások
RECORD_SECONDS=5
```

**Fontos:** Cseréld ki:
- `http://192.168.1.100:8123` - Home Assistant URL címére
- `your_long_lived_access_token_here` - A Home Assistant token-re

### 4. Rendszer indítása

```bash
cd /home/nagypal.marton/Documents/MicroPiSoundControl
docker compose build
docker compose up
```

**Első indulás ideje:** ~5-10 perc (modell letöltések)

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

## ⚙️ Környezeti változók

### Kötelező

```bash
# Home Assistant konfiguráció
HA_URL=http://192.168.1.100:8123
HA_TOKEN=your_long_lived_access_token
```

### Opcionális

```bash
# Általános beállítások
SAMPLE_RATE=16000         # Audio mintavételezési frekvencia
RECORD_SECONDS=5          # Felvétel hossza ébresztőszó után

# Wyoming service URI-k (ha más portokat használsz)
STT_URI=tcp://stt:10300
TTS_URI=tcp://piper:10200
WAKEWORD_URI=tcp://wakeword:10400

# Whisper konfiguráció
WHISPER_MODEL=tiny        # tiny/base/small/medium/large
WHISPER_LANGUAGE=hu       # hu/en
BEAM_SIZE=1               # 1-5 (magasabb = pontosabb, de lassabb)

# Piper konfiguráció
PIPER_VOICE=hu_HU-anna-medium  # Magyar Anna hang

# OpenWakeWord konfiguráció
WAKE_WORD=alexa           # Ébresztőszó
THRESHOLD=0.5             # Detektálási érzékenység (0.0-1.0)
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

### 1. "HA_TOKEN not configured"
```bash
# Ellenőrizd a .env fájlt
cat .env
# Győződj meg róla, hogy HA_TOKEN értéke helyes
# Újraindítás környezeti változókkal
docker compose down
docker compose up
```

### 2. "Cannot connect to Home Assistant"
```bash
# Ellenőrizd a Home Assistant elérhetőségét
curl http://192.168.1.100:8123/api/

# Ellenőrizd a hálózati kapcsolatot
docker exec orchestrator ping homeassistant

# Ellenőrizd a HA_URL értékét
docker exec orchestrator printenv HA_URL
```

### 3. Wake word nem érzékelhető
```bash
# Ellenőrizd a mikrofon működését
docker exec -it orchestrator python -c "import sounddevice as sd; print(sd.query_devices())"

# Csökkentsd a threshold értéket
# .env fájlban:
THRESHOLD=0.3

# Újraindítás
docker compose restart wakeword
```

### 4. STT nem működik / rossz transzkripció
```bash
# Nagyobb model használata (lassabb, de pontosabb)
# .env fájlban:
WHISPER_MODEL=base

# Beam size növelése
BEAM_SIZE=3

docker compose restart stt
```

### 5. Logok megtekintése
```bash
# Összes szolgáltatás
docker compose logs -f

# Specifikus szolgáltatás
docker compose logs -f orchestrator
docker compose logs -f stt
docker compose logs -f piper
docker compose logs -f wakeword
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
| Wyoming-Whisper (STT) | 10300 | TCP |
| Wyoming-Piper (TTS) | 10200 | TCP |
| Wyoming-OpenWakeWord | 10400 | TCP |

## 📦 Szolgáltatások részletei

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

## 📝 Konfiguráció példák

### .env fájl teljes példa

```bash
# === KÖTELEZŐ ===
# Home Assistant konfiguráció
HA_URL=http://192.168.1.100:8123
HA_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

# === OPCIONÁLIS ===
# Audio beállítások
SAMPLE_RATE=16000
RECORD_SECONDS=7

# Whisper finomhangolás
WHISPER_MODEL=base
WHISPER_LANGUAGE=hu
BEAM_SIZE=2

# Piper finomhangolás  
PIPER_VOICE=hu_HU-anna-medium

# Wake word finomhangolás
WAKE_WORD=alexa
THRESHOLD=0.4
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
