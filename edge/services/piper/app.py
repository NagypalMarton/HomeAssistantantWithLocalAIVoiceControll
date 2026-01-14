# app.py tartalma
import subprocess
import os
import sys

# Beállítások
PIPER_BINARY = "./piper/piper"
MODEL_PATH = "piper_voices/hu_HU-imre-medium.onnx"
OUTPUT_FILE = "output.wav"

def speak(text):
    print(f"🗣️ Beszéd generálása: {text}")
    
    # Parancs összeállítása
    cmd = [
        PIPER_BINARY,
        "--model", MODEL_PATH,
        "--output_file", OUTPUT_FILE
    ]
    
    try:
        # Piper hívása
        process = subprocess.run(cmd, input=text.encode('utf-8'), capture_output=True)
        
        if process.returncode != 0:
            print(f"❌ Hiba a Piper futtatásakor: {process.stderr.decode()}")
            return

        print("✅ Hangfájl kész. Lejátszás...")
        # Lejátszás (Dockerben fontos a megfelelő hangeszköz)
        subprocess.run(["aplay", OUTPUT_FILE])
        
    except Exception as e:
        print(f"❌ Hiba: {e}")

if __name__ == "__main__":
    # Ha indításkor kap argumentumot, azt mondja, ha nem, akkor az alapértelmezettet
    text_to_say = "Jelenleg nem elérhető a HOME ASSISTANT példányod! Próbáld meg később!"
    if len(sys.argv) > 1:
        text_to_say = sys.argv[1]
        
    speak(text_to_say)
