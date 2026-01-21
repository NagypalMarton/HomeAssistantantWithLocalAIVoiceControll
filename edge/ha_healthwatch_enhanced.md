# Enhanced HA Health Watcher - Használati útmutató

## Mi változott?

Az új `ha_healthwatch_enhanced.sh` script **három módon** riaszt HA elérhetetlenség esetén:

### 1. 🎤 **ASR aktivitás után azonnal**
Amikor a felhasználó beszél és az ASR (Whisper) feldolgozza a beszédet:
- Figyeli a satellite logokat ASR eseményekre
- ASR esemény után **azonnal ellenőrzi** a HA elérhetőséget
- Ha nem elérhető → **azonnal bemondja** a hibaüzenetet (cooldown nélkül)

### 2. 🔌 **Kapcsolat megszakadáskor azonnal**
Amikor a HA először válik elérhetetlenné:
- Periodikus ellenőrzés észleli a státusz változást
- **Azonnal bemondja** a hibaüzenetet (cooldown nélkül)

### 3. 🔄 **Ismételt riasztás** (cooldown-nal)
Amíg a HA offline marad:
- Percenként (vagy `ALERT_COOLDOWN` szerint) ismétli a riasztást
- Ez biztosítja, hogy hosszabb kiesés esetén is emlékeztessen

## Telepítés

### 1. Régi health watcher leállítása (ha fut)

```bash
systemctl --user stop ha-healthwatch.service
systemctl --user disable ha-healthwatch.service
```

### 2. Új systemd service létrehozása

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/ha-healthwatch-enhanced.service << 'EOF'
[Unit]
Description=Enhanced Home Assistant Health Watcher with ASR Monitoring
After=docker.service
Requires=docker.service

[Service]
Type=simple
EnvironmentFile=/home/nagypalmarton/Documents/HomeAssistantantWithLocalAIVoiceControll/edge/.env
WorkingDirectory=/home/nagypalmarton/Documents/HomeAssistantantWithLocalAIVoiceControll/edge
ExecStart=/home/nagypalmarton/Documents/HomeAssistantantWithLocalAIVoiceControll/edge/ha_healthwatch_enhanced.sh
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF
```

### 3. Service indítása

```bash
systemctl --user daemon-reload
systemctl --user enable ha-healthwatch-enhanced.service
systemctl --user start ha-healthwatch-enhanced.service
```

### 4. Státusz ellenőrzése

```bash
systemctl --user status ha-healthwatch-enhanced.service
journalctl --user -u ha-healthwatch-enhanced.service -f
```

## Konfiguráció (.env)

```bash
# Home Assistant Configuration
HA_URL=http://homeassistant.local:8123
HA_TOKEN=your_long_lived_token

# Device Configuration
DEVICE_NAME=QuickRelay371

# Enhanced Health Watcher Settings
CHECK_INTERVAL=60        # Periodikus ellenőrzés gyakorisága (mp)
ALERT_COOLDOWN=60        # Ismételt riasztások közti minimum idő (mp)
ALERT_TEXT="A Home Assistant jelenleg nem elérhető!"
```

## Működési logika

```
┌─────────────────────────────────────────────────────────┐
│           Enhanced HA Health Watcher                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Satellite Log Monitor (real-time)                   │
│     ├─ Figyeli: ASR/transcript események               │
│     └─ ASR észlelve → Azonnali HA check → Alert        │
│                                                          │
│  2. Periodic HA Monitor (60s interval)                  │
│     ├─ Folyamatos HA ping                               │
│     ├─ Státusz változás → Azonnali alert                │
│     └─ Offline marad → Cooldown szerinti ismétlés      │
│                                                          │
│  3. Alert Mechanism                                     │
│     ├─ Piper TTS: szöveg → magyar hang                  │
│     ├─ Satellite hangszóró: lejátszás                   │
│     └─ Cooldown: ismételt riasztás kezelés             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Példa működés

### Forgatókönyv 1: HA elérhető → beszél a user → HA elérhető
```
[10:00:00] Enhanced HA health monitoring started
[10:00:15] User: "Hey Jarvis, kapcsold be a lámpát"
[10:00:16] ASR activity detected in satellite logs
[10:00:16] HA check passed → No alert
[10:00:17] HA válaszol → TTS lejátszás
```

### Forgatókönyv 2: HA offline → beszél a user
```
[10:00:00] Enhanced HA health monitoring started
[10:01:00] HA connection lost → immediate alert
           🔊 "A Home Assistant jelenleg nem elérhető!"
[10:01:30] User: "Hey Jarvis, kapcsold be a lámpát"
[10:01:31] ASR activity detected in satellite logs
[10:01:31] HA check failed after ASR → immediate alert
           🔊 "A Home Assistant jelenleg nem elérhető!"
[10:02:00] Periodic check → HA still down → cooldown active
[10:03:00] Periodic check → HA still down → alert
           🔊 "A Home Assistant jelenleg nem elérhető!"
```

### Forgatókönyv 3: HA visszajön
```
[10:05:00] HA is now available (restored)
[10:05:30] User: "Hey Jarvis, kapcsold be a lámpát"
[10:05:31] ASR activity detected in satellite logs
[10:05:31] HA check passed → No alert
[10:05:32] HA válaszol → TTS lejátszás
```

## Hibaelhárítás

### Log monitoring nem működik

```bash
# Ellenőrizd, hogy a satellite konténer fut-e
docker ps | grep wyoming-satellite

# Satellite logok manuális ellenőrzése
docker logs -f wyoming-satellite
```

### Alert nem szólal meg

```bash
# Piper konténer ellenőrzése
docker ps | grep wyoming-piper

# TTS cache ellenőrzése
ls -la /home/nagypalmarton/Documents/HomeAssistantantWithLocalAIVoiceControll/edge/tts-cache/

# Hangszóró teszt
docker exec -i wyoming-satellite aplay -D plughw:4,0 -l
```

### Túl gyakori riasztások

Növeld az `ALERT_COOLDOWN` értékét:
```bash
# .env fájlban
ALERT_COOLDOWN=120  # 2 percenként max
```

## Visszaállás az egyszerű verzióra

```bash
systemctl --user stop ha-healthwatch-enhanced.service
systemctl --user disable ha-healthwatch-enhanced.service
systemctl --user enable ha-healthwatch.service
systemctl --user start ha-healthwatch.service
```

## Előnyök az egyszerű verzióhoz képest

| Funkció | Egyszerű | Enhanced |
|---------|----------|----------|
| Periodikus ellenőrzés | ✅ | ✅ |
| ASR utáni azonnali riasztás | ❌ | ✅ |
| Kapcsolat megszakadás riasztás | ❌ | ✅ |
| Satellite log monitoring | ❌ | ✅ |
| Cooldown kezelés | ✅ | ✅ (intelligensebb) |
| Dupla alert elkerülés | Részben | ✅ |
