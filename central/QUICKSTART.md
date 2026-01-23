# 🚀 Central Backend - TL;DR Gyors Indítás

## 1 perc alatt futó rendszer

### Windows (PowerShell)
```powershell
cd central
.\start.ps1
docker exec central-ollama ollama pull ministral-3:3b-instruct-2512-q4_K_M
```

### Linux/Mac
```bash
cd central
chmod +x start.sh
./start.sh
docker exec central-ollama ollama pull ministral-3:3b-instruct-2512-q4_K_M
```

**Ennyi! ✅**

---

## Mi történik automatikusan?

1. ✅ Létrejön a `.env` fájl (ha nincs)
2. ✅ Generálódik biztonságos `JWT_SECRET` (32 byte random)
3. ✅ Generálódik `ENCRYPTION_KEY` (Fernet kulcs)
4. ✅ Elindul az összes Docker service:
   - PostgreSQL (adatbázis)
   - Redis (cache)
   - Ollama (LLM, GPU-val)
   - User API (intent processing)
   - HA Manager (per-user HA instances)
5. ✅ Health check-ek (várj 5 másodpercet)

---

## Tesztelés

```bash
# Health checks
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/api/v1/health
curl http://localhost:11434/api/tags

# Intent test (dummy token)
curl -X POST http://localhost:8000/api/v1/intent \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000000",
    "device_id": "test-device",
    "text": "Kapcsold be a nappali lámpát"
  }'
```

---

## Leállítás

```bash
docker-compose down
```

---

## Újraindítás (már fut)

```bash
docker-compose restart
```

---

## Teljes reset (törli az adatbázist is!)

```bash
docker-compose down -v
rm .env
./start.sh  # vagy start.ps1
```

---

## Troubleshooting

### Port már foglalt (8000, 8001, etc.)
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

### GPU nem működik
```bash
# Ellenőrzés
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# Ha nem megy, telepítsd az NVIDIA Docker Runtime-ot
```

### Ollama modell letöltés lassú
```bash
# ~2GB letöltés, várj türelemmel
docker exec central-ollama ollama pull ministral-3:3b-instruct-2512-q4_K_M

# Ellenőrzés
docker exec central-ollama ollama list
```

---

**🎉 Kész! A Central Backend fut!**
