# 1. Bevezetés

## 1.1 Cél
A dokumentum célja a **Mikrobi** nevű, mesterséges intelligencián alapuló okosotthon-vezérlő rendszer teljes és naprakész szoftverkövetelmény-specifikációjának rögzítése. A rendszer hang- és szövegalapú vezérlést biztosít, edge–cloud architektúrában, DevOps szemlélettel megvalósítva.

## 1.2 Hatókör
A specifikáció lefedi:
- Raspberry Pi-alapú edge komponenseket (Wyoming protokoll használatával)
- Központi backend és LLM-alapú döntési logikát
- Home Assistant integrációt (Conversation API)
- Konténerizált (Docker, Kubernetes) futtatási környezetet
- Automatizált infrastruktúrát (Terraform)
- Monitorozást (Zabbix)
- Wyoming protokoll alapú voice assistant szolgáltatásokat

A dokumentum **nem tér ki** olyan jövőbeli funkciókra, amelyek a beszélgetés során kifejezetten kizárásra kerültek.

## 1.3 Definíciók
- **HA**: Home Assistant
- **LLM**: Large Language Model
- **Edge**: Raspberry Pi 4 (2 GB RAM)
- **Wake-word**: „Mikrobi”

---

# 2. Rendszeráttekintés

## 2.1 Magas szintű architektúra
A rendszer két fő részből áll:

- **Edge réteg** (Raspberry Pi): Wyoming protokoll alapú hangfeldolgozó szolgáltatások
  - Wyoming-OpenWakeWord: Wake-word detektálás
  - Wyoming-Whisper: Speech-to-Text (STT)
  - Wyoming-Piper: Text-to-Speech (TTS)
  - Orchestrator: Szolgáltatások koordinálása és HA kommunikáció
  - Config Web: Home Assistant kapcsolat konfigurálása

- **Központi réteg**: Kubernetes-alapú backend, LLM, Home Assistant instance-ok és adminisztráció
  - Home Assistant instance-ok (felhasználónként)
  - LLM szolgáltatás (Ollama - tervezett)
  - Admin és felhasználói felületek (tervezett)
  - Monitoring (Zabbix - tervezett)

A Raspberry Pi **nem kommunikál közvetlenül IoT eszközökkel**, kizárólag a hozzá rendelt Home Assistant REST API-n (Conversation API) keresztül.

## 2.2 Wyoming protokoll
A rendszer Wyoming protokollt használ a voice assistant szolgáltatások közötti kommunikációhoz:
- **Egységes interfész**: Különböző szolgáltatások közös protokollal
- **TCP socket alapú**: Event-based architektúra
- **Home Assistant natív támogatás**: Közvetlen integráció

### Service portok
| Szolgáltatás | Port | Protokoll |
|--------------|------|-----------|
| Config Web | 8000 | HTTP |
| Wyoming-Whisper (STT) | 10300 | TCP/Wyoming |
| Wyoming-Piper (TTS) | 10200 | TCP/Wyoming |
| Wyoming-OpenWakeWord | 10400 | TCP/Wyoming |

## 2.3 Adatfolyam
```
Mikrofon → Wyoming-OpenWakeWord (Wake-word detektálás)
              ↓ (wake detected)
         Orchestrator (audio felvétel)
              ↓ (audio)
         Wyoming-Whisper (STT)
              ↓ (magyar szöveg)
         Home Assistant Conversation API
              ↓ (válasz szöveg)
         Wyoming-Piper (TTS)
              ↓ (audio)
         Hangszóró
```

---

# 3. Funkcionális követelmények (FR)

## 3.1 Felhasználókezelés
- FR-1: A rendszer támogassa a felhasználók regisztrációját (vezetéknév, keresztnév, tartózkodási hely, jelszó).
- FR-2: Regisztráció után automatikusan létrejön egy dedikált Home Assistant instance.
- FR-3: A felhasználó kizárólag a saját HA instance-ához férhet hozzá.
- FR-4: Fiók törlés esetén a hozzá tartozó HA instance véglegesen törlődik.

## 3.2 Hangalapú vezérlés (Edge)
- FR-5: A Raspberry Pi folyamatosan figyelje a wake-wordöt.
  - **Jelenlegi implementáció**: "Alexa" (Wyoming-OpenWakeWord)
  - **Tervezett**: "Mikrobi" (egyedi magyar modell)
- FR-6: Wake-word után aktiválódjon a magyar nyelvet támogató ASR szolgáltatás (Wyoming-Whisper, faster-whisper backend).
- FR-7: Egy Raspberry Pi egy felhasználót és egy HA instance-t szolgál ki.
- FR-8: A wake-word felismerés és az ASR **külön komponensként** működjön (Wyoming protokoll).
- FR-9: A rendszer használjon Text-to-Speech szolgáltatást a válaszok hangos visszajelzéséhez (Wyoming-Piper, hu_HU-anna-medium modell).

## 3.3 Szöveges vezérlés
- FR-10: A rendszer támogassa a szöveges parancsokat webes felületen keresztül.
- FR-11: A szöveges és hangalapú parancsok azonos intent-feldolgozási folyamaton menjenek keresztül.

## 3.4 Intent feldolgozás és LLM
- FR-12: A rendszer a **Home Assistant Conversation API**-t használja az intent feldolgozáshoz.
  - **Jelenlegi implementáció**: Home Assistant natív intent kezelés (eszközvezérlés, automatizmusok)
  - **Opcionális**: AI asszisztensek integrációja (Google AI, OpenAI, helyi LLM-ek)
- FR-13: Csak a **nem explicit**, kontextuális parancsok kerüljenek az LLM-hez (pl. „sötét van a konyhában").
- FR-14: Az explicit parancsokat (pl. „kapcsold fel a lámpát") a rendszer közvetlen HA-hívássá alakítsa.
- FR-15: **Tervezett LLM integráció**: Az LLM az Ollama platformon futó **Ministral 3 3B** modell legyen.
- FR-16: **Tervezett**: Az LLM központi, megosztott instance legyen logikai izolációval (request-szintű context).
- FR-17: **Tervezett**: Az LLM hozzáférjen a teljes HA állapothoz és konfigurációhoz.

## 3.5 Orchestrator és koordináció
- FR-18: Legyen egy központi orchestrator komponens, amely koordinálja a Wyoming szolgáltatásokat.
- FR-19: Az orchestrator kezelje a mikrofon felvételt a wake-word detektálás után.
- FR-20: Az orchestrator kommunikáljon a Home Assistant Conversation API-val.
- FR-21: A rendszer játssza le a TTS által generált válaszokat a hangszórón keresztül.

## 3.6 Konfigurációs szolgáltatás
- FR-22: A rendszer biztosítson webes felületet (Config Web) a Home Assistant kapcsolat konfigurálásához.
- FR-23: A konfiguráció támogassa a Home Assistant URL és Long-Lived Access Token megadását.
- FR-24: A konfiguráció perzisztensen tárolódjon és az orchestrator számára elérhető legyen.
- FR-25: A konfigurációs felület magyar nyelvű legyen.

## 3.7 Automatizmusok
- FR-26: **Tervezett**: Az LLM képes legyen Home Assistant automatizmusok létrehozására.
- FR-27: **Tervezett**: Minden automatizmus létrehozása **felhasználói jóváhagyáshoz kötött**.

## 3.8 Biztonságkritikus műveletek
- FR-28: Zárak és egyéb biztonsági eszközök vezérlése megerősítést igényel.
- FR-29: A rendszer minden esetben adjon hang- vagy szöveges visszajelzést.

## 3.9 Hibatűrés
- FR-30: Ha a Home Assistant vagy az LLM nem érhető el, a Raspberry Pi tájékoztassa a felhasználót a sikertelenség okáról.

---

# 4. Nem funkcionális követelmények (NFR)

## 4.1 Teljesítmény
- NFR-1: Wake-word felismerési késleltetés < 500 ms.
- NFR-2: LLM válaszidő < 3 másodperc.

## 4.2 Megbízhatóság
- NFR-3: A rendszer 99%-os rendelkezésre állást célozzon.

## 4.3 Biztonság
- NFR-4: A rendszer interneten keresztül érhető el, hitelesítéssel.
- NFR-5: Hang- és szöveges adatok **nem tárolhatók**, azonnal törlésre kerülnek.

## 4.4 Karbantarthatóság
- NFR-6: Minden komponens konténerizált legyen.
- NFR-7: Verziózott API-k használata kötelező.

---

# 5. DevOps és üzemeltetés

## 5.1 Konténerizáció és orchestráció
- Docker minden komponenshez
- Kubernetes a központi infrastruktúrában

## 5.2 Automatizálás
- Terraform az infrastruktúra (HA instance-ok, backend szolgáltatások) létrehozásához

## 5.3 Frissítések
- Raspberry Pi: **OS és konténerek automatikusan frissülnek**
- Backend és egyéb szolgáltatások: admin által engedélyezve

## 5.4 Monitorozás
- Zabbix központi telepítéssel
- Monitorozott elemek:
  - Kubernetes és Docker komponensek
  - Home Assistant API
  - Ollama / LLM metrikák
  - Raspberry Pi lightweight HTTP exporter

---

# 6. Adminisztrációs felületek

- Admin UI: üzemeltetési és felhasználókezelési funkciók
- Felhasználói UI:
  - Bejelentkezés / regisztráció
  - Saját HA instance URL megjelenítése (URL **nem** tartalmazza a „mikrobi” szót)

---

# 7. Korlátozások és feltételezések

- Egy Raspberry Pi egy felhasználót szolgál ki
- A Raspberry Pi nem vezérel közvetlen IoT eszközöket
- GPU elérhető a központi LLM futtatásához

---

# 8. Összegzés

A Mikrobi rendszer egy edge–cloud alapú, biztonságos és skálázható okosotthon-megoldás, amely modern DevOps eszközökre, LLM-alapú intelligenciára és Home Assistant ökoszisztémára épül. A specifikáció az aktuálisan elfogadott követelményeket teljes körűen rögzíti.

