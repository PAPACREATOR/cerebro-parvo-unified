"""Deterministic LAB flow proposal built from verified Wiki context.

This is not a production flow engine. It binds a human-selected sequence of
already-known capabilities to a Wiki context packet and returns a candidate
plan with source hashes. It cannot execute tools, mutate Store, approve, or
promote.
"""
from __future__ import annotations

import hashlib

from nexus.contracts import Blocked
from nexus.lab.wiki.context_packet import check_packet, raw_json


ALLOWED_STEPS = ("verify", "interpret", "proofread", "convert_pdf")
MAX_STEPS = 8


def _digest(value) -> str:
    return hashlib.sha256(raw_json(value)).hexdigest()


def propose(packet: dict, steps: list[str]) -> dict:
    check_packet(packet)
    if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_STEPS:
        raise Blocked("Sequência de flow inválida.")
    if any(not isinstance(step, str) or step not in ALLOWED_STEPS for step in steps):
        raise Blocked("Capability de flow não autorizada.")
    if len(steps) != len(set(steps)):
        raise Blocked("Flow experimental não aceita passos duplicados nesta versão.")

    source_refs = [
        {
            "run_id": source["run_id"],
            "authority": source["authority"],
            "content_sha256": source["content_sha256"],
            "provenance_sha256": source["provenance_sha256"],
            "process_id": source["process_id"],
        }
        for source in packet["sources"]
    ]
    plan = {
        "version": 1,
        "kind": "LAB_FLOW_CANDIDATE",
        "authority": "NONE",
        "objective": packet["objective"],
        "steps": list(steps),
        "sources": source_refs,
        "context_sha256": _digest(packet),
    }
    plan["plan_sha256"] = _digest(plan)
    return plan


def validate_proposal(packet: dict, plan: dict) -> dict:
    check_packet(packet)
    if not isinstance(plan, dict) or set(plan) != {
        "version", "kind", "authority", "objective", "steps", "sources",
        "context_sha256", "plan_sha256",
    }:
        raise Blocked("Proposta de flow inválida.")

    expected_hash = plan["plan_sha256"]
    unsigned = dict(plan)
    unsigned.pop("plan_sha256")
    if expected_hash != _digest(unsigned):
        raise Blocked("Proposta de flow adulterada.")

    if plan["version"] != 1 or plan["kind"] != "LAB_FLOW_CANDIDATE" or plan["authority"] != "NONE":
        raise Blocked("Autoridade de flow inválida.")
    if plan["objective"] != packet["objective"] or plan["context_sha256"] != _digest(packet):
        raise Blocked("Contexto do flow mudou.")

    rebuilt = propose(packet, list(plan["steps"]))
    if rebuilt != plan:
        raise Blocked("Proposta de flow não corresponde às fontes verificadas.")
    return plan
