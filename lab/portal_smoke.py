"""Check the locally running GoliathApp portal (apps/platform-host) against the lab database.

Uses the local-only dev sign-in (GOLIATH_PLATFORM_HOST_DEV_LOGIN=1), which GoliathApp refuses in
production. Never point this at a shared or production portal.

    GOLIATH_PORTAL_URL=http://127.0.0.1:3400 \
    GOLIATH_PLATFORM_HOST_DEV_LOGIN_SECRET=... python lab/portal_smoke.py
"""

from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import urllib.parse
import urllib.request

EXPECTED = {
    "omics.institution.list": ("name", "ENA"),
    "omics.patient.list": ("external_id", "HG00621"),
    "omics.sample.list": ("sample_name", "canary-SRR28293403-linear-subset"),
}


def _opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def _call(opener, base: str, path: str, *, body: dict | None = None, headers: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method="POST" if data or headers else "GET")
    req.add_header("content-type", "application/json")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    with opener.open(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def run(base: str, secret: str, scope_id: str = "1") -> list[str]:
    host = urllib.parse.urlparse(base).hostname
    if host not in {"127.0.0.1", "localhost", "portal"}:
        raise SystemExit(f"refusing non-local portal {host!r}: the dev sign-in is for the local lab only")
    opener = _opener()
    report: list[str] = []
    health = _call(opener, base, "/api/health")
    assert health.get("status") == "ok", health
    report.append(f"health ok ({health.get('service')})")
    _call(
        opener,
        base,
        "/api/session/dev-establish",
        body={},
        headers={"x-goliath-dev-login-secret": secret, "x-goliath-dev-login-scope-id": scope_id},
    )
    me = _call(opener, base, "/api/session/me")
    assert me.get("activeRoleName") == "organization_admin", me
    report.append(f"signed in as {me.get('fullName')} ({me.get('activeRoleName')}, scope {me.get('activeScopeId')})")
    nav = json.dumps(_call(opener, base, "/api/navigation"))
    for path in ("/app/omics/patients", "/app/omics/samples", "/app/omics/institutions"):
        assert path in nav, f"navigation is missing {path}"
    report.append("navigation shows the /app/omics branch")
    for request_code, (field, value) in EXPECTED.items():
        rows = _call(opener, base, "/api/portal/semantic/run", body={"requestCode": request_code, "params": {}})["rows"]
        assert [r[field] for r in rows] == [value], (request_code, rows)
        report.append(f"{request_code}: {value}")
    return report


def main() -> int:
    base = os.environ.get("GOLIATH_PORTAL_URL", "http://127.0.0.1:3400").rstrip("/")
    secret = os.environ.get("GOLIATH_PLATFORM_HOST_DEV_LOGIN_SECRET")
    if not secret:
        print("Set GOLIATH_PLATFORM_HOST_DEV_LOGIN_SECRET (the value the local portal was started with).", file=sys.stderr)
        return 2
    for line in run(base, secret, os.environ.get("GOLIATH_LAB_SCOPE_ID", "1")):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
