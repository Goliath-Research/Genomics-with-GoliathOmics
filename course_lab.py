"""Course lab helper for Genomics with GoliathOmics.

    python course_lab.py init      # write .env with random local-only credentials (once)
    python course_lab.py up        # start PostgreSQL 19 and run the official seed (idempotent)
    python course_lab.py portal    # start the GoliathApp portal (dev mode) on 127.0.0.1:3400
    python course_lab.py smoke     # check the portal shows the public ENA rows
    python course_lab.py status    # lab row counts
    python course_lab.py psql      # open psql on the lab database
    python course_lab.py sql FILE  # run a course .sql file against the lab database
    python course_lab.py test      # live pytest checks against the running lab (add --portal for the portal)
    python course_lab.py down      # stop and delete the lab (volumes included)

Everything runs through `docker compose` on this machine and binds to 127.0.0.1.
Credentials stay in .env (git-ignored) and are never printed.
"""

from __future__ import annotations

import os
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
GENERATED = ("LAB_PG_SUPERUSER_PASSWORD", "GOLIATH_PORTAL_DB_PASSWORD", "GOLIATH_PLATFORM_HOST_DEV_LOGIN_SECRET")


def read_env(path: Path = ENV_FILE) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def init(path: Path = ENV_FILE, example: Path = ROOT / ".env.example") -> list[str]:
    """Create or complete .env; fill empty generated values with random hex. Returns keys filled."""
    lines = (path if path.exists() else example).read_text().splitlines()
    filled: list[str] = []
    out: list[str] = []
    for line in lines:
        key, sep, value = line.partition("=")
        if sep and key.strip() in GENERATED and not value.strip():
            line = f"{key.strip()}={secrets.token_hex(24)}"
            filled.append(key.strip())
        out.append(line)
    old_umask = os.umask(0o077)
    try:
        path.write_text("\n".join(out) + "\n")
    finally:
        os.umask(old_umask)
    path.chmod(0o600)
    return filled


def compose(*args: str) -> int:
    return subprocess.call(["docker", "compose", *args], cwd=ROOT)


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "init":
        filled = init()
        print(f".env ready ({len(filled)} value(s) generated; values not shown)")
        return 0
    if cmd in {"up", "portal", "smoke"} and not ENV_FILE.exists():
        init()
    if cmd == "up":
        return compose("up", "-d", "db") or compose("run", "--rm", "--build", "seed")
    if cmd == "portal":
        return compose("--profile", "portal", "up", "-d", "portal")
    if cmd == "smoke":
        env = read_env()
        os.environ.setdefault("GOLIATH_PORTAL_URL", f"http://127.0.0.1:{env.get('LAB_PORTAL_PORT', '3400')}")
        os.environ["GOLIATH_PLATFORM_HOST_DEV_LOGIN_SECRET"] = env.get("GOLIATH_PLATFORM_HOST_DEV_LOGIN_SECRET", "")
        sys.path.insert(0, str(ROOT / "lab"))
        import portal_smoke

        return portal_smoke.main()
    if cmd == "test":
        env = read_env()
        os.environ["GOLIATH_LAB_DSN"] = (
            f"host=127.0.0.1 port={env.get('LAB_PG_PORT', '55419')} user=postgres dbname=goliath_omics_lab "
            f"password={env.get('LAB_PG_SUPERUSER_PASSWORD', '')}"
        )
        selector = []
        if "--portal" in argv[2:]:
            os.environ.setdefault("GOLIATH_PORTAL_URL", f"http://127.0.0.1:{env.get('LAB_PORTAL_PORT', '3400')}")
            os.environ["GOLIATH_PLATFORM_HOST_DEV_LOGIN_SECRET"] = env.get("GOLIATH_PLATFORM_HOST_DEV_LOGIN_SECRET", "")
        else:
            selector = ["-k", "not portal"]
        return subprocess.call([sys.executable, "-m", "pytest", "-m", "live", "-rs", *selector], cwd=ROOT)
    if cmd == "status":
        with (ROOT / "lab" / "sql" / "90_verify_lab.sql").open() as sql:
            return subprocess.call(
                ["docker", "compose", "exec", "-T", "db", "psql", "-U", "postgres", "-d", "goliath_omics_lab"],
                cwd=ROOT,
                stdin=sql,
            )
    if cmd == "sql":
        if len(argv) < 3:
            print("usage: python course_lab.py sql FILE.sql")
            return 2
        with Path(argv[2]).open() as sql:
            return subprocess.call(
                ["docker", "compose", "exec", "-T", "db", "psql", "-X", "-U", "postgres", "-d", "goliath_omics_lab"],
                cwd=ROOT,
                stdin=sql,
            )
    if cmd == "psql":
        return compose("exec", "db", "psql", "-U", "postgres", "-d", "goliath_omics_lab")
    if cmd == "down":
        return compose("--profile", "portal", "--profile", "seed", "down", "-v")
    print(__doc__)
    return 0 if cmd == "help" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
