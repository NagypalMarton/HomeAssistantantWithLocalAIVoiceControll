# Software Requirements Specification (SRS)
## PiSmartSpeaker - Home Assistant Voice Satellite

**Verzió:** 1.0  
**Dátum:** 2026. január 17.  
**Szerző:** Nagypal Márton

---

## 1. Bevezetés

### 1.1 Cél
Ez a dokumentum a PiSmartSpeaker rendszer szoftverkövetelményeit specifikálja. A rendszer egy Raspberry Pi alapú hangvezérlésű satellite eszköz, amely magyar nyelven kommunikál egy cloudban futó Home Assistant rendszerrel.

### 1.2 Alkalmazási terület
Otthoni környezet, átlagfelhasználók számára, akik magyar nyelvű hangvezérlést szeretnének Home Assistant okosotthon rendszerükhöz.

### 1.3 Definíciók és rövidítések
- **HA**: Home Assistant
- **VAD**: Voice Activity Detection (Hangaktivitás-észlelés)
- **ASR**: Automatic Speech Recognition (Beszédfelismerés)
- **TTS**: Text-to-Speech (Szöveg-beszéd átalakítás)
- **LLM**: Large Language Model
- **Wake Word**: Ébresztőszó (Hey Jarvis)

---

## 2. Általános leírás

### 2.1 Termék perspektíva
A PiSmartSpeaker egy független satellite eszköz, amely Wyoming protokollon keresztül csatlakozik egy cloudban futó Home Assistant példányhoz. A rendszer offline beszédfelismerést és szintézist használ, de a parancsok feldolgozása és válaszok generálása a HA LLM-jén keresztül történik.

### 2.2 Termék funkciók
- Ébresztőszó felismerés ("Hey Jarvis")
- Magyar nyelvű beszédfelismerés
- Kommunikáció Home Assistant rendszerrel
- Magyar nyelvű hangvisszajelzés
- Kapcsolódási hiba kezelése

### 2.3 Felhasználói karakterisztikák
- **Cél felhasználó**: Átlagos technikai ismeretekkel rendelkező háztartási felhasználó
- **Felhasználási környezet**: Otthoni környezet (nappali, konyha, hálószoba)
- **Eszköz-felhasználó arány**: 1:1 (egy eszköz egy felhasználóhoz)

### 2.4 Korlátozások
- Raspberry Pi 4 B 2GB hardveres erőforrás-korlátozások
- Internet kapcsolat szükséges a HA kommunikációhoz
- Csak magyar nyelv támogatása
- Egy eszköz csak egy Home Assistant példányhoz csatlakozhat

---

## 3. Rendszer követelmények

### 3.1 Funkcionális követelmények

#### 3.1.1 Ébresztőszó felismerés
**REQ-F-001**: A rendszernek folyamatosan figyelnie kell a "Hey Jarvis" ébresztőszót.  
**REQ-F-002**: Az ébresztőszó felismerése után a rendszer aktiválódik és megkezdi a parancs rögzítését.  
**REQ-F-003**: Az ébresztőszó felismerés offline módon kell működjön.

#### 3.1.2 Beszédfelismerés
**REQ-F-004**: A rendszernek magyar nyelvű beszédet kell szöveggé alakítania.  
**REQ-F-005**: A beszédfelismerés offline módon kell működjön (Whisper tiny-int8 modell).  
**REQ-F-006**: VAD (Voice Activity Detection) használata szükséges a pontos beszéd szegmentáláshoz.  
**REQ-F-007**: A beszédrögzítés automatikusan befejeződik, ha 2 másodpercig nincs beszéd.

#### 3.1.3 Home Assistant kommunikáció
**REQ-F-008**: A felismert szöveget el kell küldeni a Home Assistant LLM-nek feldolgozásra.  
**REQ-F-009**: A rendszernek fogadnia kell a HA LLM válaszát.  
**REQ-F-010**: Csak az LLM által generált válaszokat szabad visszaadni, egyéb feldolgozás nélkül.  
**REQ-F-011**: A kommunikáció Wyoming protokollon keresztül történik.

#### 3.1.4 Szöveg-beszéd szintézis
**REQ-F-012**: A HA LLM válaszát magyar nyelvű beszéddé kell alakítani.  
**REQ-F-013**: A TTS hangja "hu_HU-imre-medium" (magyar férfi hang).  
**REQ-F-014**: A TTS offline módon kell működjön (Piper).

#### 3.1.5 Hibakezelés
**REQ-F-015**: Ha a Home Assistant nem elérhető, a rendszernek a következő üzenetet kell lejátszania: *"A Home Assistant jelenleg nem elérhető."*  
**REQ-F-016**: Időtúllépés esetén (5 másodperc) ugyanaz a hibaüzenet szólaljon meg.  
**REQ-F-017**: A rendszer a hibaüzenet után visszatér az ébresztőszó figyelés állapotába.

---

### 3.2 Nem-funkcionális követelmények

#### 3.2.1 Teljesítmény
**REQ-NF-001**: Az ébresztőszó felismerés késleltetése maximum 500 ms lehet.  
**REQ-NF-002**: A beszédfelismerés valós idejű legyen (RTF < 0.5).  
**REQ-NF-003**: A teljes interakció (ébresztőszó → kérdés → válasz lejátszása) 5 másodpercnél gyorsabb kell legyen (HA válaszidő nélkül).  
**REQ-NF-004**: A TTS szintézis késleltetése maximum 1 másodperc lehet.

#### 3.2.2 Megbízhatóság
**REQ-NF-005**: A rendszernek 99% uptime-ot kell biztosítania helyi hálózati kapcsolat esetén.  
**REQ-NF-006**: Áramkimaradás után a rendszer automatikusan újraindul és működőképes állapotba kerül.  
**REQ-NF-007**: A Docker konténerek "restart: unless-stopped" politikával rendelkeznek.

#### 3.2.3 Használhatóság
**REQ-NF-008**: A rendszer konfigurálása nem igényelhet speciális technikai ismereteket.  
**REQ-NF-009**: A hangvisszajelzés tisztán érthető és természetes hangzású legyen.  
**REQ-NF-010**: Az ébresztőszó felismerés hamis pozitív aránya legfeljebb 1/óra.

#### 3.2.4 Biztonság és adatvédelem
**REQ-NF-011**: A helyi beszédfelismerés és TTS offline működik, nem küld hangfelvételt külső szerverekre.  
**REQ-NF-012**: Csak a felismert szöveg kerül továbbításra a Home Assistant felé.  
**REQ-NF-013**: A Home Assistant kapcsolat titkosított (HTTPS/WSS) legyen.

#### 3.2.5 Karbantarthatóság
**REQ-NF-014**: A rendszer Docker konténereken alapul az egyszerű frissítés érdekében.  
**REQ-NF-015**: A modellek és konfigurációk külön kötetekben (volumes) tárolódnak.  
**REQ-NF-016**: Logok elérhetők Docker logs paranccsal.

---

## 4. Külső interfész követelmények

### 4.1 Hardver interfészek
**REQ-HW-001**: USB mikrofon (plughw:3,0) 16kHz, mono, 16-bit PCM formátumban.  
**REQ-HW-002**: USB hangszóró (plughw:4,0) 22050Hz, mono, 16-bit PCM formátumban.  
**REQ-HW-003**: Ethernet vagy WiFi kapcsolat a HA eléréshez.

### 4.2 Szoftver interfészek
**REQ-SW-001**: Wyoming OpenWakeWord szerver (TCP 10400).  
**REQ-SW-002**: Wyoming Whisper szerver (TCP 10300).  
**REQ-SW-003**: Wyoming Piper szerver (TCP 10200).  
**REQ-SW-004**: Home Assistant Wyoming Integration (távoli kapcsolat).

### 4.3 Kommunikációs interfészek
**REQ-COM-001**: Wyoming protokoll használata a komponensek közötti kommunikációhoz.  
**REQ-COM-002**: TCP/IP alapú hálózati kommunikáció.

---

## 5. Rendszer architektúra

### 5.1 Komponensek

```
┌─────────────────────────────────────────────────────────┐
│                   Wyoming Satellite                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Mikrofon    │  │  Hangszóró   │  │     VAD      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────┬────────────┬────────────┬─────────────────┘
              │            │            │
         ┌────▼────┐  ┌────▼────┐  ┌───▼─────┐
         │  Wake   │  │ Whisper │  │  Piper  │
         │  Word   │  │  (ASR)  │  │  (TTS)  │
         └─────────┘  └─────────┘  └─────────┘
                           │            ▲
                           │            │
                      ┌────▼────────────┴─────┐
                      │   Home Assistant      │
                      │   (Cloud + LLM)       │
                      └───────────────────────┘
```

### 5.2 Működési folyamat

1. **Idle állapot**: OpenWakeWord figyeli az ébresztőszót
2. **Wake**: "Hey Jarvis" észlelése → Satellite aktiválás
3. **Listen**: VAD alapján hangrögzítés amíg beszél a felhasználó
4. **Transcribe**: Whisper átalakítja szöveggé a hangot
5. **Process**: Szöveg elküldése HA LLM-nek
6. **Respond**: HA LLM válasz fogadása
7. **Speak**: Piper TTS lejátssza a választ
8. **Return to Idle**: Visszatérés az 1. lépéshez

---

## 6. Rendszer modellek

### 6.1 Használt AI modellek
- **OpenWakeWord**: `hey_jarvis.tflite` - Ébresztőszó detekció
- **Whisper**: `tiny-int8` - Magyar beszédfelismerés (gyors, alacsony erőforrás)
- **Piper**: `hu_HU-imre-medium` - Magyar TTS szintézis
- **Home Assistant LLM**: Távoli, HA által konfigurált modell

---

## 7. Telepítési követelmények

### 7.1 Hardver
- Raspberry Pi 4 Model B (minimum 2GB RAM)
- USB mikrofon
- USB hangszóró vagy aktív hangszórók
- 16GB+ microSD kártya
- Stabil tápegység (5V/3A)
- Ethernet vagy WiFi kapcsolat

### 7.2 Szoftver
- Raspberry Pi OS (64-bit ajánlott)
- Docker Engine
- Docker Compose

### 7.3 Hálózat
- Internet kapcsolat
- Hozzáférés a Home Assistant cloud példányhoz
- Wyoming Integration konfigurált HA-ban

---

## 8. Elfogadási kritériumok

### 8.1 Funkcionális tesztek
- ✅ Az ébresztőszó ("Hey Jarvis") 95%-os pontossággal felismerésre kerül
- ✅ Magyar nyelvű parancsok helyesen kerülnek felismerésre
- ✅ A HA LLM válaszai pontosan visszajátszásra kerülnek
- ✅ Kapcsolódási hiba esetén a hibaüzenet elhangzik

### 8.2 Teljesítmény tesztek
- ✅ Teljes interakció idő < 5 másodperc (HA nélkül)
- ✅ CPU használat < 80% működés közben
- ✅ Memória használat < 1.5GB

### 8.3 Megbízhatósági tesztek
- ✅ 24 órás folyamatos működés hiba nélkül
- ✅ Újraindítás után automatikus helyreállás
- ✅ Hálózatkiesés esetén helyes viselkedés

---

## 9. Függőségek és kockázatok

### 9.1 Függőségek
- Home Assistant cloud elérhetősége
- Wyoming Integration működése
- Stabil internet kapcsolat
- Docker hub elérhetősége (első telepítéskor)

### 9.2 Kockázatok
- **Hálózati késleltetés**: A cloud HA válaszideje befolyásolja a felhasználói élményt
- **Modell pontossága**: A tiny modell korlátozott pontossága zajos környezetben
- **Hardver kompatibilitás**: USB audio eszközök eszközazonosítói változhatnak
- **HA API változások**: Wyoming Integration változásai kompatibilitási problémákat okozhatnak

---

## 10. Jövőbeli fejlesztési lehetőségek

- Többfelhasználós támogatás (hangazonosítás)
- Egyéb ébresztőszavak támogatása
- Helyi történet/cache a gyakori kérdésekhez
- LED visszajelzés az állapotokról
- Többszobás szinkronizáció
- Nagyobb Whisper modell opcionális használata (jobb pontosság)
- Angol nyelv támogatás

---

## 11. Dokumentum jóváhagyás

| Szerepkör | Név | Dátum | Aláírás |
|-----------|-----|-------|---------|
| Projekt tulajdonos | Nagypal Márton | 2026.01.17 | |
| Rendszermérnök | | | |
| Tesztvezető | | | |

---

**Verzióelőzmények:**

| Verzió | Dátum | Szerző | Változások |
|--------|-------|--------|------------|
| 1.0 | 2026.01.17 | Nagypal Márton | Kezdeti verzió |
