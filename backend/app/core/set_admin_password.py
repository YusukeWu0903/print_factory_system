"""Set or rotate the local administrator password without storing plaintext."""

import argparse
from getpass import getpass
from pathlib import Path
import secrets

from app.core.config import BACKEND_DIR
from app.core.passwords import hash_password


def save_password_hash(env_path: Path, password_hash: str) -> None:
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    lines = [line for line in lines if not line.strip().startswith("ADMIN_PASSWORD_HASH=")]
    lines.append(f"ADMIN_PASSWORD_HASH={password_hash}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set the print factory administrator password")
    parser.add_argument("--generate", action="store_true", help="Generate and print a strong password once")
    args = parser.parse_args()

    if args.generate:
        password = secrets.token_urlsafe(24)
    else:
        password = getpass("New administrator password (at least 12 characters): ")
        if password != getpass("Repeat password: "):
            raise SystemExit("Passwords do not match")
        if len(password) < 12:
            raise SystemExit("Password must be at least 12 characters")

    save_password_hash(BACKEND_DIR / ".env", hash_password(password))
    print("Administrator password hash saved to backend/.env")
    if args.generate:
        print(f"One-time administrator password: {password}")


if __name__ == "__main__":
    main()
