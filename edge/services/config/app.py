#!/usr/bin/env python3
"""
Configuration Web Service
Home Assistant TOKEN és URL konfigurálása
"""
import os
import json
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Configuration paths
CONFIG_DIR = Path(os.getenv("CONFIG_DIR", "/app/config"))
CONFIG_FILE = CONFIG_DIR / "ha_config.json"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load configuration from JSON file"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[config] Error loading config: {e}")
    return {"ha_url": "", "ha_token": ""}


def save_config(data: dict):
    """Save configuration to JSON file"""
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[config] Configuration saved to {CONFIG_FILE}")


@app.route("/")
def index():
    """Serve configuration page"""
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/config", methods=["GET"])
def get_config():
    """Get current configuration"""
    config = load_config()
    return jsonify({
        "ha_url": config.get("ha_url", ""),
        "ha_token": "***" if config.get("ha_token") else "",  # Don't expose token
        "configured": bool(config.get("ha_url") and config.get("ha_token"))
    })


@app.route("/api/config", methods=["POST"])
def set_config():
    """Save configuration"""
    data = request.get_json() or {}
    
    ha_url = (data.get("ha_url", "") or "").strip()
    ha_token = (data.get("ha_token", "") or "").strip()
    
    # Validation
    errors = []
    
    if not ha_url:
        errors.append("Home Assistant URL nem lehet üres")
    elif not (ha_url.startswith("http://") or ha_url.startswith("https://")):
        errors.append("URL-nek http:// vagy https:// prefixszel kell kezdődnie")
    
    if not ha_token:
        errors.append("Home Assistant TOKEN nem lehet üres")
    elif len(ha_token) < 20:
        errors.append("TOKEN túl rövid (minimum 20 karakter)")
    
    if errors:
        return jsonify({"status": "error", "message": " | ".join(errors)}), 400
    
    # Save config
    config = {
        "ha_url": ha_url,
        "ha_token": ha_token
    }
    save_config(config)
    
    return jsonify({
        "status": "ok",
        "message": "Konfiguráció mentve! Az orchestrator csatlakozik a Home Assistant-hoz."
    }), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check"""
    config = load_config()
    is_configured = bool(config.get("ha_url") and config.get("ha_token"))
    return jsonify({"status": "ok", "configured": is_configured})


HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MicroPi Voice Control - Home Assistant Beállítás</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 40px;
            max-width: 500px;
            width: 100%;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            color: #333;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        input[type="text"],
        input[type="url"],
        textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.3s;
            font-family: monospace;
        }
        
        input[type="text"]:focus,
        input[type="url"]:focus,
        textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        textarea {
            resize: vertical;
            min-height: 80px;
            font-family: monospace;
            font-size: 12px;
        }
        
        .help-text {
            color: #888;
            font-size: 12px;
            margin-top: 6px;
            line-height: 1.5;
        }
        
        .code {
            background: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: monospace;
            color: #d63384;
        }
        
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        button:active:not(:disabled) {
            transform: translateY(0);
        }
        
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .message {
            margin-top: 20px;
            padding: 12px;
            border-radius: 6px;
            display: none;
            font-size: 14px;
        }
        
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            display: block;
        }
        
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            display: block;
        }
        
        .status {
            margin-top: 20px;
            padding: 12px;
            background: #f5f5f5;
            border-radius: 6px;
            font-size: 13px;
            color: #666;
            text-align: center;
        }
        
        .status.configured {
            background: #d4edda;
            color: #155724;
        }
        
        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 6px;
            background: #999;
        }
        
        .status.configured .status-dot {
            background: #28a745;
        }
        
        .guide {
            margin: 20px 0;
            padding: 15px;
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            border-radius: 4px;
            font-size: 13px;
            line-height: 1.6;
        }
        
        .guide strong {
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ MicroPi Voice Control</h1>
        <p class="subtitle">Home Assistant integráció beállítása</p>
        
        <div class="guide">
            <strong>1. Home Assistant URL:</strong> Pl. <span class="code">http://192.168.1.100:8123</span><br>
            <strong>2. Long-Lived Token:</strong> Profil → Long-Lived Access Tokens
        </div>
        
        <form id="configForm">
            <div class="form-group">
                <label for="haUrl">Home Assistant URL</label>
                <input
                    type="url"
                    id="haUrl"
                    name="haUrl"
                    placeholder="http://192.168.1.100:8123"
                    required
                >
                <div class="help-text">
                    🌐 Hol érhető el a Home Assistant?<br>
                    Pl.: <span class="code">http://192.168.1.100:8123</span> vagy <span class="code">https://home.example.com</span>
                </div>
            </div>
            
            <div class="form-group">
                <label for="haToken">Home Assistant Long-Lived Access Token</label>
                <textarea
                    id="haToken"
                    name="haToken"
                    placeholder="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                    required
                ></textarea>
                <div class="help-text">
                    🔐 Titkos token - nem kerül el a szervertől!<br>
                    Home Assistant → Profil → Long-Lived Access Tokens → Create Token
                </div>
            </div>
            
            <button type="submit">💾 Konfiguráció Mentése</button>
        </form>
        
        <div id="message" class="message"></div>
        <div id="status" class="status"></div>
    </div>
    
    <script>
        // Load existing config
        async function loadConfig() {
            try {
                const response = await fetch('/api/config');
                const data = await response.json();
                if (data.ha_url) {
                    document.getElementById('haUrl').value = data.ha_url;
                }
                updateStatus(data.configured);
            } catch (error) {
                console.error('Hiba a konfiguráció betöltésekor:', error);
            }
        }
        
        // Update status display
        function updateStatus(isConfigured) {
            const statusEl = document.getElementById('status');
            if (isConfigured) {
                statusEl.className = 'status configured';
                statusEl.innerHTML = '<span class="status-dot"></span>✅ Konfigurálva - az orchestrator csatlakozik a Home Assistant-hoz';
            } else {
                statusEl.className = 'status';
                statusEl.innerHTML = '<span class="status-dot"></span>⏳ Konfigurálásra vár...';
            }
        }
        
        // Show message
        function showMessage(text, type) {
            const msgEl = document.getElementById('message');
            msgEl.textContent = text;
            msgEl.className = 'message ' + type;
            if (type === 'success') {
                setTimeout(() => {
                    msgEl.className = 'message';
                }, 3000);
            }
        }
        
        // Handle form submission
        document.getElementById('configForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const haUrl = document.getElementById('haUrl').value.trim();
            const haToken = document.getElementById('haToken').value.trim();
            const button = e.target.querySelector('button');
            
            if (!haUrl || !haToken) {
                showMessage('❌ Mindkét mező kitöltése kötelező!', 'error');
                return;
            }
            
            button.disabled = true;
            button.textContent = '⏳ Mentés...';
            
            try {
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ ha_url: haUrl, ha_token: haToken })
                });
                
                const result = await response.json();
                
                if (!response.ok) {
                    showMessage('❌ ' + result.message, 'error');
                    button.disabled = false;
                    button.textContent = '💾 Konfiguráció Mentése';
                    return;
                }
                
                showMessage('✅ ' + result.message, 'success');
                updateStatus(true);
                document.getElementById('haToken').value = ''; // Clear token from UI
                button.disabled = false;
                button.textContent = '💾 Konfiguráció Mentése';
            } catch (error) {
                showMessage('❌ Hálózati hiba: ' + error.message, 'error');
                button.disabled = false;
                button.textContent = '💾 Konfiguráció Mentése';
            }
        });
        
        // Load config on page load
        loadConfig();
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
