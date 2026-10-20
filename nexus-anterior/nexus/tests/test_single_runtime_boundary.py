"""Guard the optional Node transport without duplicating Nexus authority.

The existing Python app/Host/Store own interpretation, execution, memory and
Canonical approval. The gateway may only forward HTTP to that existing boundary.
No production Kernel, parser, Host or Store is modified.
"""

import hashlib
import json
from pathlib import Path

NEXUS = Path(__file__).resolve().parents[1]
REPOSITORY = NEXUS.parent


def test_only_python_host_owns_execution_and_memory():
    for name in ("app.py", "host.py", "store.py", "frontdoor.py"):
        assert (NEXUS / name).is_file(), name

    gateway = (REPOSITORY / "server.js").read_text(encoding="utf-8")
    assert "hostname: HOST, port: BACKEND_PORT" in gateway
    assert "http.request(" in gateway
    assert "127.0.0.1" in gateway
    assert "0.0.0.0" not in gateway
    assert "X-Nexus-Session" in gateway
    assert "res.writeHead(upstreamResponse.statusCode || 502" in gateway

    ARCHIVE_REDACTED_04 = (
        "new Map(", "parseFrontdoor(", "proposeOperation(",
        "generateSimplePdf(", "frontdoor_rules.json", "crypto.randomUUID(",
        "approvalTickets", "preexecutionTickets", "artifacts.set(",
        "run.status = 'PASS'", "run.status = \"PASS\"",
        "canonical.mkdir(", "MAJOR_CAPABILITY_SERVER_SIDE_GEMINI_API",
    )
    for fragment in ARCHIVE_REDACTED_04:
        assert fragment not in gateway, fragment

    package = json.loads((REPOSITORY / "package.json").read_text(encoding="utf-8"))
    assert package["scripts"]["start"] == "node server.js"
    assert package["dependencies"] == {"express": "4.21.2"}
    assert not (REPOSITORY / "metadata.json").exists()


def test_folha_html_matches_host_integrity_manifest():
    manifest = json.loads((NEXUS / "integrity.json").read_text(encoding="utf-8"))
    html = (NEXUS / "ui" / "index.html").read_bytes()
    assert hashlib.sha256(html).hexdigest() == manifest["ui/index.html"], (
        "The Folha HTML changed without its existing Host integrity seal."
    )


def test_gateway_does_not_claim_local_approval_or_store():
    gateway = (REPOSITORY / "server.js").read_text(encoding="utf-8")
    assert "req.pipe(upstream)" in gateway
    assert "pipeline(upstreamResponse, res," in gateway
    assert "/api/confirm-run" in gateway
    assert "/api/approve" in gateway
    assert "/api/runs" in gateway
    assert "(?:runs|pdf)" in gateway
    assert "res.json({ status: 'PASS'" not in gateway
