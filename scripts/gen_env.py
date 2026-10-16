import secrets
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = REPO_ROOT / ".env.example"
TARGET_ENV = REPO_ROOT / ".env"

def generate_secure_secrets() -> dict[str, str]:
    return {
        "SECRET_KEY": secrets.token_hex(32),
        "API_AUTH_TOKEN": secrets.token_urlsafe(24),
        "POSTGRES_USER": "copper_admin",
        "POSTGRES_PASSWORD": secrets.token_urlsafe(24),
        "POSTGRES_DB": "copperdb",
        "REDIS_PASSWORD": secrets.token_urlsafe(24),
        "CHROMA_TOKEN": secrets.token_hex(24),
    }

def main():
    print("==================================================")
    print("COPPER Environment Configuration Generator")
    print("==================================================")

    if TARGET_ENV.exists():
        print(f"[!] Existing .env file found at {TARGET_ENV}")
        choice = input("Do you want to overwrite it with newly generated secrets? [y/N]: ").strip().lower()
        if choice != "y":
            print("[*] Aborting without modifying existing .env.")
            sys.exit(0)

    if not ENV_EXAMPLE.exists():
        print(f"[x] Error: Reference template {ENV_EXAMPLE} not found.")
        sys.exit(1)

    sec = generate_secure_secrets()
    template_text = ENV_EXAMPLE.read_text(encoding="utf-8")

    for key, val in sec.items():
        pattern_old = f"{key}=CHANGE_ME"
        if pattern_old in template_text:
            template_text = template_text.replace(pattern_old, f"{key}={val}")

    generated_block = f"""
# ------------------------------------------------------------------------------
# AUTOMATICALLY GENERATED CRYPTOGRAPHIC SECRETS (scripts/gen_env.py)
# ------------------------------------------------------------------------------
API_AUTH_TOKEN={sec['API_AUTH_TOKEN']}
POSTGRES_USER={sec['POSTGRES_USER']}
POSTGRES_PASSWORD={sec['POSTGRES_PASSWORD']}
POSTGRES_DB={sec['POSTGRES_DB']}
REDIS_PASSWORD={sec['REDIS_PASSWORD']}
CHROMA_TOKEN={sec['CHROMA_TOKEN']}
"""
    full_env_content = template_text.strip() + "\n" + generated_block

    TARGET_ENV.write_text(full_env_content, encoding="utf-8")
    print(f"[+] Successfully generated secure configuration at: {TARGET_ENV}")
    print("[+] Cryptographically random keys created:")
    print(f"    - SECRET_KEY:        {sec['SECRET_KEY'][:8]}... (64 hex characters)")
    print(f"    - API_AUTH_TOKEN:    {sec['API_AUTH_TOKEN'][:8]}... (secure bearer)")
    print(f"    - POSTGRES_PASSWORD: {sec['POSTGRES_PASSWORD'][:6]}... (database password)")
    print(f"    - REDIS_PASSWORD:    {sec['REDIS_PASSWORD'][:6]}... (in-memory cache password)")
    print(f"    - CHROMA_TOKEN:      {sec['CHROMA_TOKEN'][:8]}... (vector store token)")

if __name__ == "__main__":
    main()
