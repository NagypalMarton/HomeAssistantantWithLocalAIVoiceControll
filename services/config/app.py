import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

# Configuration paths
CONFIG_DIR = Path(os.getenv("CONFIG_DIR", "/app/config"))
CONFIG_FILE = CONFIG_DIR / "forward_url.json"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


class ConfigRequest(BaseModel):
    forward_url: str


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"forward_url": ""}


def save_config(data: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)


@app.get("/")
async def index():
    index_path = Path(os.getenv("INDEX_HTML_PATH", "/app/index.html"))
    if not index_path.exists():
        return HTMLResponse("<h1>Configuration Page</h1><p>Index file not found</p>")
    with open(index_path, "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/config")
async def get_config():
    config = load_config()
    return JSONResponse(config)


@app.post("/api/config")
async def set_config(req: ConfigRequest):
    if not req.forward_url or not req.forward_url.strip():
        raise HTTPException(status_code=400, detail="FORWARD_URL nem lehet üres")
    
    # Validáció: szimpla URL format check
    if not (req.forward_url.startswith("http://") or req.forward_url.startswith("https://")):
        raise HTTPException(status_code=400, detail="URL-nek http:// vagy https:// prefixszel kell kezdődnie")
    
    config = {"forward_url": req.forward_url.strip()}
    save_config(config)
    print(f"[config] FORWARD_URL mentve: {req.forward_url}")
    return JSONResponse({"status": "ok", "message": "Konfiguráció mentve. Az orchestrator elindul."})


@app.get("/health")
async def health():
    config = load_config()
    is_configured = bool(config.get("forward_url", "").strip())
    return JSONResponse({"status": "ok", "configured": is_configured})
