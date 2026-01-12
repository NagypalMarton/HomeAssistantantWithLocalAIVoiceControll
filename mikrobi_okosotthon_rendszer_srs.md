# 1. Bevezetés

## 1.1 Cél
A dokumentum célja a **Mikrobi** nevű, mesterséges intelligencián alapuló okosotthon-vezérlő rendszer teljes és naprakész szoftverkövetelmény-specifikációjának rögzítése. A rendszer hang- és szövegalapú vezérlést biztosít, edge–cloud architektúrában, DevOps szemlélettel megvalósítva.

## 1.2 Hatókör
A specifikáció lefedi:
- Raspberry Pi-alapú edge komponenseket
- Központi backend és LLM-alapú döntési logikát
- Home Assistant integrációt
- Konténerizált (Docker, Kubernetes) futtatási környezetet
- Automatizált infrastruktúrát (Terraform)
- Monitorozást (Zabbix)

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

- **Edge réteg**: Raspberry Pi-n futó hangfeldolgozó és kommunikációs szolgáltatások
- **Központi réteg**: Kubernetes-alapú backend, LLM, Home Assistant instance-ok és adminisztráció

A Raspberry Pi **nem kommunikál közvetlenül IoT eszközökkel**, kizárólag a hozzá rendelt Home Assistant REST API-n keresztül.

---

# 3. Funkcionális követelmények (FR)

## 3.1 Felhasználókezelés
- FR-1: A rendszer támogassa a felhasználók regisztrációját (vezetéknév, keresztnév, tartózkodási hely, jelszó).
- FR-2: Regisztráció után automatikusan létrejön egy dedikált Home Assistant instance.
- FR-3: A felhasználó kizárólag a saját HA instance-ához férhet hozzá.
- FR-4: Fiók törlés esetén a hozzá tartozó HA instance véglegesen törlődik.

## 3.2 Hangalapú vezérlés (Edge)
- FR-5: A Raspberry Pi folyamatosan figyelje a „Mikrobi” wake-wordöt.
- FR-6: Wake-word után aktiválódjon a magyar és angol nyelvet támogató ASR szolgáltatás.
- FR-7: Egy Raspberry Pi egy felhasználót és egy HA instance-t szolgál ki.
- FR-8: A wake-word felismerés és az ASR **külön komponensként** működjön.

## 3.3 Szöveges vezérlés
- FR-9: A rendszer támogassa a szöveges parancsokat webes felületen keresztül.
- FR-10: A szöveges és hangalapú parancsok azonos intent-feldolgozási folyamaton menjenek keresztül.

## 3.4 Intent feldolgozás és LLM
- FR-11: Csak a **nem explicit**, kontextuális parancsok kerüljenek az LLM-hez (pl. „sötét van a konyhában”).
- FR-12: Az explicit parancsokat (pl. „kapcsold fel a lámpát”) a rendszer közvetlen HA-hívássá alakítsa.
- FR-13: Az LLM az Ollama platformon futó **Ministral 3 3B** modell legyen.
- FR-14: Az LLM központi, megosztott instance legyen logikai izolációval (request-szintű context).
- FR-15: Az LLM hozzáférjen a teljes HA állapothoz és konfigurációhoz.

## 3.5 Automatizmusok
- FR-16: Az LLM képes legyen Home Assistant automatizmusok létrehozására.
- FR-17: Minden automatizmus létrehozása **felhasználói jóváhagyáshoz kötött**.

## 3.6 Biztonságkritikus műveletek
- FR-18: Zárak és egyéb biztonsági eszközök vezérlése megerősítést igényel.
- FR-19: A rendszer minden esetben adjon hang- vagy szöveges visszajelzést.

## 3.7 Hibatűrés
- FR-20: Ha az LLM nem érhető el, a Raspberry Pi tájékoztassa a felhasználót a sikertelenség okáról.

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

