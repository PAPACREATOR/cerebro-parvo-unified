"""Loopback-only Folha Nexus server using the Python standard library."""
import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import socket
import sqlite3
import sys
import threading
import time
import unicodedata
import webbrowser
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from nexus.contracts import ROOT, Blocked, strict_json, validate
from nexus.frontdoor import parse, propose_operation
from nexus.capability_router import declared_router, registered_router
from nexus.adapters.constitutional import build_molde
from nexus.host import Host
from nexus.instance import data_directory_lock
from nexus.store import atomic


_PREEXECUTION_TTL_SECONDS = 180
_MAX_PREEXECUTION_TICKETS = 64

# Laboratory code is not in Host.verify_integrity()'s fixed required set.
# Pin its exact audited bytes here: app.py itself is Host-sealed. Never import
# mutable experimental code into the product without verifying these digests.
_PINNED_WIKI_LAB = {
    "lab/wiki/kernel_bridge.py": "078fd05c7ec0e9ebeb05500f8c536c374b38d57482fe753578fb96b60e2ac5c9",
    "lab/wiki/context_packet.py": "ff16ae99dc74637ca59f66c788fc39bb68cbc47eb3462a1d024bce005269c0d0",
}


_PINNED_GRAPH_SHA256 = "ac9a972c5a3b066285c6eb2a478c15a4d32eddec123af29e21ba1b41e5bfeb33"


def _verified_wiki_bridge(store):
    for relative, expected in _PINNED_WIKI_LAB.items():
        target = ROOT / relative
        if target.is_symlink() or target.is_junction() or not target.is_file():
            raise Blocked("Componente de pesquisa não autorizado.")
        if not secrets.compare_digest(hashlib.sha256(target.read_bytes()).hexdigest(), expected):
            raise Blocked("A integridade do módulo FTS5 mudou; pesquisa bloqueada.")
    # Reuse the original laboratory's Store verification and FTS5 implementation.
    from nexus.lab.wiki.kernel_bridge import WikiBridge

    # Derived SQLite index must be outside the sovereign Store and Git tree.
    index_root = store.root.parent / (store.root.name + "-fts5-index")
    if index_root.is_symlink() or index_root.is_junction():
        raise Blocked("Índice de pesquisa redirecionado.")
    return WikiBridge(store, index_root)


def _verified_graph(store):
    # The graph is a derived index, not an authority. Pin its audited source.
    module = ROOT / "graph" / "graph_minimo.py"
    if (module.is_symlink() or module.is_junction() or not module.is_file()
            or not secrets.compare_digest(hashlib.sha256(module.read_bytes()).hexdigest(),
                                          _PINNED_GRAPH_SHA256)):
        raise Blocked("Integridade do grafo alterada; pesquisa bloqueada.")
    from nexus.graph.graph_minimo import GraphMinimo

    root = store.root.parent / (store.root.name + "-fts5-index")
    file = root / "graph.sqlite"
    if root.is_symlink() or root.is_junction() or file.is_symlink() or file.is_junction():
        raise Blocked("Índice de relações redirecionado.")
    return GraphMinimo(file)


def _request_digest(request):
    raw = json.dumps(
        request, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _composite_plan(text):
    """Read-only, bounded multi-capability proposal. No grant or dispatch."""
    if type(text) is not str or not text.strip() or len(text) > 12000:
        return None
    normal = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()
    if normal.startswith("& "):
        normal = normal[2:].strip()
    normal = normal.strip(" .!?")
    recipes = {
        "verifica este documento e converte-o em pdf": ("convert_pdf", "converter para pdf"),
        "verifica a integridade deste documento e converte para pdf": ("convert_pdf", "converter para pdf"),
        "verificar integridade de ficheiro e converter para pdf": ("convert_pdf", "converter para pdf"),
        "verifica este texto e revê o português": ("proofread", "rever texto"),
        "verifica a integridade deste texto e revê o português": ("proofread", "rever texto"),
        "verificar integridade de ficheiro e rever texto": ("proofread", "rever texto"),
    }
    target = recipes.get(normal)
    if target is None:
        return None
    router = declared_router()
    first = router.recognise_command("verificar integridade de ficheiro")
    second = router.recognise_command(target[1])
    if first is None or second is None or (first.process, second.process) != ("verify", target[0]):
        raise Blocked("Receita composta não corresponde ao registo fechado.")
    return {
        "authority": "NONE",
        "execution": "NOT_AUTHORIZED",
        "requires_human_confirmation": True,
        "steps": [
            {"process": first.process, "command": first.command},
            {"process": second.process, "command": second.command},
        ],
    }

# ... (app.py continues unchanged from upstream) ...
