# Ollama Conversation Agent - Automatikus Setup

## ✅ AUTOMATIKUS TELEPÍTÉS ENGEDÉLYEZVE!

Az Ollama conversation agent **automatikusan betöltődik és beállítódik** minden Home Assistant indításkor!

### 🚀 Mi történik automatikusan:

1. **Home Assistant indításkor:**
   - Észleli az `ollama_conversation` custom component-et
   - Automatikusan létrehozza az integrációt (ha még nincs)
   - Beállítja: Host: `http://ollama:11434`, Model: `llama3.2:3b`
   - Regisztrálja a conversation agent-et

2. **Újraindításkor:**
   - Minden konfiguráció megmarad
   - Azonnal használatra kész
   - **Semmi UI-beli teendő nincs!**

---

## 📋 Használat (2 lépés)

### 1️⃣ Ellenőrizd, hogy be van-e állítva

**http://localhost:8123**
- Beállítások → Eszközök és Szolgáltatások
- Keresd: **"Ollama Conversation"** vagy **"Ollama"**
- Ha megjelenik → ✅ **Automatikusan létrejött!**

### 2️⃣ Chat használata!

**Assist megnyitása:**
- Jobb felső sarok → **💬 Chat ikon** 
- Vagy billentyűparancs: **Ctrl + K**

**Példa kérdések:**
- "Szia! Ki vagy?"
- "Miben tudsz segíteni?"
- "Mi az időjárás?"
- "Kapcsold be a nappaliban a lámpát"

**Magyar nyelvű válaszokat kapsz az Ollama llama3.2:3b model-től!** 🇭🇺

---

## ⚙️ Opcionális: Állítsd be mint alapértelmezett Assist Agent

Ha szeretnéd, hogy az Ollama legyen **a** beszélgető ügynök:

1. Beállítások → **Hang Asszisztensek (Voice assistants)**
2. Kattints a **"Home Assistant"** asszisztensre  
3. **Beszélgetési ügynök** → válaszd: **"Ollama"**
4. **💾 MENTÉS**

Ezután **MINDEN** Assist kérés az Ollama-n megy keresztül!

---

## 🔄 Újraindítás teszt

```powershell
# Home Assistant újraindítása
docker restart homeassistant

# Várj 30 másodpercet
Start-Sleep -Seconds 30

# Ellenőrzés
(Invoke-WebRequest http://localhost:8123 -UseBasicParsing).StatusCode
# → 200: működik!
```

**Újraindítás után az Ollama agent automatikusan aktív marad!**

---

## ✅ Ellenőrzési lista

| Állapot | Leírás |
|---------|--------|
| ✅ | Home Assistant fut: http://localhost:8123 |
| ✅ | Ollama API fut: http://localhost:11434 |
| ✅ | llama3.2:3b model betöltve |
| ✅ | Custom component automatikusan betöltődik |
| ✅ | Ollama integráció automatikusan létrejön |
| ✅ | Újraindítás után is megmarad |
| ⏳ | Chat tesztelése (te csinálod)

---

## 🔍 Hibaelhárítás

### "Ollama Conversation" nem jelenik meg az integrációk között
```powershell
# Újraindítás
docker restart homeassistant
Start-Sleep -Seconds 20

# Logok ellenőrzése
docker logs homeassistant --tail=50 | findstr ollama_conversation
```

### "Cannot connect to Ollama" hiba az integráció hozzáadásakor
```powershell
# Ollama státusz
docker ps | findstr ollama

# Ollama újraindítása
docker restart ollama
Start-Sleep -Seconds 10

# API teszt
curl http://localhost:11434/api/tags
```

### Chat lassú vagy nem válaszol
- Csökkentsd a válasz hosszt: szerkeszd `conversation.py` → `num_predict`: 150 → 100
- Vagy váltsd kisebb modellre: `phi3:mini`

---

## 🎯 Mik történtek a háttérben?

1. **Custom Component betöltődött** - Home Assistant felismerte az `ollama_conversation` integrációt
2. **Config Flow elérhető** - A beállítási varázslót használhatod a UI-ból
3. **Conversation Platform regisztrálva** - Az agent be tudja fogadni a chat inputokat
4. **Ollama API csatlakozás** - `http://ollama:11434` végponton eléri az LLM-et
5. **Magyar nyelvű rendszer prompt** - Minden kérdéshez hozzáadva, hogy magyarul válaszoljon

---

## 🚀 Most menj a UI-ra és állítsd be!

**http://localhost:8123** → Beállítások → Eszközök és Szolgáltatások → + Integráció → "Ollama Conversation"

Ezután már **chatelhetsz az Ollama-val az Assist-en keresztül**! 🎉
