# Ollama Conversation Agent - Használati útmutató

## ✅ Sikeresen telepítve!

A custom Ollama conversation agent betöltődött a Home Assistant-ba. Most már be tudod állítani az Assist-ben.

## 📋 Lépések az Ollama mint Assist Agent beállításához

### 1. Home Assistant megnyitása
Nyisd meg: **http://localhost:8123**

### 2. Ollama Integration hozzáadása

1. Menü → **Beállítások (Settings)** → **Eszközök és Szolgáltatások (Devices & Services)**
2. Kattints a jobb alsó sarokban a **+ INTEGRÁCIÓ HOZZÁADÁSA** gombra
3. Keresd meg: **"Ollama Conversation"**
4. Add meg az alábbi adatokat:
   - **Ollama Host URL**: `http://ollama:11434`
   - **Model neve**: `llama3.2:3b`
5. Kattints **KÜLDÉS (Submit)**

### 3. Ollama beállítása mint alapértelmezett Assist Agent

1. Menü → **Beállítások (Settings)** → **Hang Asszisztensek (Voice assistants)**
2. Kattints a **Home Assistant** asszisztensre
3. A **Beszélgetési ügynök (Conversation agent)** menüpontban válaszd ki: **Ollama**
4. Kattints **MENTÉS (Save)**

### 4. Assist használata Ollama-val

**Módszer 1: Chat interfész**
- Kattints a jobb felső sarokban a **mikrofonra** vagy **chat ikonra**
- Írj be kérdést magyarul: 
  - "Szia! Ki vagy?"
  - "Miben tudsz segíteni?"
  - "Mi az időjárás?"
- Az Ollama llama3.2:3b modell fog válaszolni

**Módszer 2: Voice (opcionális)**
- Ha van mikrofonod, beszélj be
- Az Ollama fogja feldolgozni a szöveget és válaszolni

**Módszer 3: Dashboard**
- Menü → **Ollama Chat** nézet
- Használd a gyors gombokat vagy az input mezőt

## 🔍 Ellenőrzés

### Ollama agent státusz ellenőrzése:
```powershell
# Logok
docker logs homeassistant --tail=50 | findstr ollama

# Ollama API teszt
curl http://localhost:11434/api/generate -d "{\"model\":\"llama3.2:3b\",\"prompt\":\"Hello\",\"stream\":false}"
```

### Home Assistant elérhető:
```powershell
(Invoke-WebRequest http://localhost:8123 -UseBasicParsing).StatusCode
# Should return: 200
```

## 🎯 Mit fog csinálni az Ollama Agent?

1. **Minden Assist kérdés** → Ollama llama3.2:3b model dolgozza fel
2. **Magyar nyelven** válaszol
3. **Smart home context** - okos otthon asszisztensként viselkedik
4. **Helyi futás** - minden adat a gépeden marad, nincs cloud

## ⚙️ Testreszabás

### Model váltása:
1. Beállítások → Eszközök és Szolgáltatások → Ollama Conversation
2. Kattints **CONFIGURE**
3. Válts modelt: `phi3:mini` vagy `qwen2.5:3b`

### System prompt módosítása:
Szerkeszd: `custom_components/ollama_conversation/conversation.py` fájlban a prompt-ot

### További modellek telepítése:
```powershell
docker exec ollama ollama pull phi3:mini
docker exec ollama ollama pull qwen2.5:3b
```

## 🐛 Hibaelhárítás

### "Ollama Conversation" nem jelenik meg az integrációk között:
```powershell
# Újraindítás
docker restart homeassistant

# Logok ellenőrzése
docker logs homeassistant 2>&1 | findstr "ollama_conversation"
```

### "Cannot connect to Ollama":
```powershell
# Ollama státusz
docker ps | findstr ollama

# Ollama újraindítása
docker restart ollama
```

### Válasz túl lassú:
- Csökkentsd a `num_predict` értéket (150 → 100)
- Váltsd kisebb modellre: `phi3:mini`

## 📂 Fájlok

- **Custom component**: `config/home-assistant/custom_components/ollama_conversation/`
- **Configuration**: `config/home-assistant/configuration.yaml`
- **Dashboard**: `config/home-assistant/ui-lovelace.yaml`
- **Scripts**: `config/home-assistant/scripts.yaml`

## 🎉 Sikeres használat jele

Ha minden működik:
1. Assist chat-ben írsz egy kérdést magyarul
2. 2-5 másodperc múlva értelmes választ kapsz magyarul
3. A válasz kontextusában érthető és hasznos
4. Logokban nincs ERROR az ollama_conversation-nél

Most már **chatelhetsz az Assist-tel Ollama segítségével**! 🚀
