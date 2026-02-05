# Implementacios terv (Central)

**Datum:** 2026-02-05

Ez a terv a diploma kovetelmenyeihez igazodva bontja fel a megvalositas hianyzo reszeit. A lepesek prioritas sorrendben vannak, a korai blokkok alapokat raknak le a kesobbi fejezetekhez es a meresekhez.

## 1) Funkcionalis alapok lezarasa (backend core)

### 1.1 User es Auth perzisztencia
- Adatbazis modellek: felhasznalo, refresh token, session
- Regisztracio: jelszo hash, role alapertelmezessel
- Login: jelszo ellenorzes, token kiadas
- Refresh: token forgatas, blacklist tamogatas
- Logout: token blacklist

### 1.2 Session context es Redis
- Session context mentes/olvasas (rolling window)
- Token blacklist Redisben
- Rate limiting kulcsok (user/device/IP)

### 1.3 Audit log perzisztalas
- Intent kereses es HA valaszok mentese
- Latency, status, error kodok tarolasa
- Admin query lehetosegek

### 1.4 HA Manager adatbazis integracio
- Instance letrehozas/mentes (user_id, container_id, port, status)
- Port foglalas DB alapjan
- Torles DB + Docker sync
- Valos status lekerdezes Dockerbol

## 2) HA vegrehajtasi utvonal

### 2.1 User -> HA instance feloldasa
- User HA URL + token kezelese
- Biztonsagos token tarolas/letoltes

### 2.2 HA API hivasok
- Alap parancs vegrehajtas (turn_on, turn_off, set)
- Hibakezeles (timeout, 4xx/5xx)
- Idempotens vegrehajtas alapok

### 2.3 Intent -> HA mapping
- Intent JSON validalas
- Entity feloldas
- Valasz generacio HA eredmeny alapjan

## 3) Admin felulet es jogosultsag

### 3.1 Admin API
- Felhasznalok listazasa, letiltasa
- HA instance lista es status
- Audit log listazas es szures

### 3.2 UI (minimum scope)
- Bejelentkezes (ADMIN)
- Felhasznalo kezelo oldal
- Instance status nezet
- Audit log nezet

### 3.3 RBAC
- ADMIN vs USER
- Admin-only endpoint vedelme

## 4) Eroforras meres es metrikak

### 4.1 Per-container metrics
- Docker stats / cAdvisor + Prometheus
- CPU, memoria, IO, GPU (ha elerheto)

### 4.2 Per-user aggregacio
- user_id label a metrikakban
- HA instance metrikak osszerendelese

### 4.3 Terheles es meres
- Terheles generator (N user, N request/perc)
- Latency, atfutas, hibaarany
- Skala hatarok felderitese

## 5) Teszteles es dokumentalt meres

### 5.1 Unit tesztek
- Auth, intent parsing, HA manager

### 5.2 Integration tesztek
- Docker Compose alapon
- LLM es HA emulacio ha kell

### 5.3 Meresi riport
- Grafikonok, tablazatok
- Kovetkeztetesek (latency, skala, eroforras)

## Javasolt utemezes (hetek)

- **Het 1-2:** 1) Funkcionalis alapok lezarasa
- **Het 3:** 2) HA vegrehajtasi utvonal
- **Het 4:** 3) Admin felulet + RBAC
- **Het 5:** 4) Metrikak es terheles
- **Het 6:** 5) Tesztek es meresi riport
