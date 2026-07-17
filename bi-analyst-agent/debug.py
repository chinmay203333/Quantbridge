import os
from dotenv import load_dotenv
from pathlib import Path

# Explicitly point to the .env file relative to this script
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

token = os.getenv("HF_TOKEN")
print(f".env path used: {env_path}")
print(f".env exists: {env_path.exists()}")
print(f"HF_TOKEN found: {token is not None}")
print(f"HF_TOKEN value: {repr(token)}")