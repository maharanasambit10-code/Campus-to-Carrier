import os
from pathlib import Path

BASE_DIR = Path(r"C:\Users\bapun\OneDrive\Desktop\BPUT")
env_path = BASE_DIR / ".env"
with open(env_path, "r", encoding="utf-8") as f:
    env_content = f.read()

env_content = env_content.replace("USE_MYSQL=True", "USE_MYSQL=False")
with open(env_path, "w", encoding="utf-8") as f:
    f.write(env_content)
