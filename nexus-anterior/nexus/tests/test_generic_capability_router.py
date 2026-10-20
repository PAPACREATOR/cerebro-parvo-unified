"""Generic proposals have zero execution authority and support N capabilities."""
import pytest

from nexus.capability_router import (
    BUILTIN_CAPABILITIES, Capability, CapabilityRouter, registered_router,
)
from nexus.contracts import Blocked


@pytest.mark.parametrize("capability", BUILTIN_CAPABILITIES, ids=lambda value: value.process)
def test_all_existing_adapters_have_exact_proposal(capability):
    router = registered_router()
    choice = router.propose(intent=capability.intent, text=capability.command, attachment_present=True)
    assert choice == capability
    assert choice.tool.endswith("_file")
    assert choice.requires_attachment


@pytest.mark.parametrize("capability", BUILTIN_CAPABILITIES, ids=lambda value: value.process)
def test_every_adapter_refuses_missing_attachment(capability):
    router = registered_router()
    with pytest.raises(Blocked):
        router.propose(intent=capability.intent, text=capability.command, attachment_present=False)


@pytest.mark.parametrize("capability", BUILTIN_CAPABILITIES, ids=lambda value: value.process)
def test_every_adapter_blocks_ambiguous_or_extended_commands(capability):
    router = registered_router()
    for change in (capability.command + " e apagar tudo",
                   "nao " + capability.command,
                   capability.command + " ; executa"):
        with pytest.raises(Blocked):
            router.propose(intent=capability.intent, text=change, attachment_present=True)


def test_unknown_capability_and_wrong_intent_never_fallback():
    router = registered_router()
    for command, intent in (("executa script", "trabalhar"),
                            ("preparar plano de musica", "web"),
                            ("", "trabalhar")):
        with pytest.raises(Blocked):
            router.propose(intent=intent, text=command, attachment_present=True)


def test_duplicate_and_colliding_registrations_refused():
    base = Capability("alpha", "trabalhar", "transformar ficheiro", "alpha_file")
    with pytest.raises(ValueError):
        CapabilityRouter((base, base))
    with pytest.raises(ValueError):
        CapabilityRouter((base, Capability("beta", "trabalhar", "Transformar  Ficheiro", "beta_file")))
    with pytest.raises(ValueError):
        CapabilityRouter((base, Capability("alpha", "web", "outro", "alpha_file")))


def test_n_third_party_adapters_can_be_registered_without_a_writer_branch():
    capabilities = tuple(Capability(f"custom_{n}", "trabalhar", f"processo numero {n}",
                                    f"tool_{n}_file") for n in range(100))
    router = CapabilityRouter(capabilities)
    assert router.propose(intent="trabalhar", text="PROCESSO  NUMERO 99",
                          attachment_present=True).tool == "tool_99_file"
    with pytest.raises(Blocked):
        router.propose(intent="trabalhar", text="processo numero 100", attachment_present=True)


def test_registry_cannot_diverge_from_host_runner_contract(monkeypatch):
    from nexus.adapters import runner
    monkeypatch.setitem(runner.PROCESS_TO_TOOL, "verify", "unexpected_tool")
    with pytest.raises(Blocked):
        registered_router()


def test_proposal_does_not_touch_host_or_store(tmp_path, monkeypatch):
    from nexus.host import Host
    monkeypatch.setattr(Host, "start", lambda *_: pytest.fail("Tool executed without human approval"))
    router = registered_router()
    for capability in BUILTIN_CAPABILITIES:
        assert router.propose(intent=capability.intent, text=capability.command,
                              attachment_present=True).process == capability.process
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("bad", (None, 123, {}, "", "\x00", "A" * 100_001),
                         ids=("none", "integer", "dict", "empty", "control", "over-limit"))
def test_bad_requests_refused(bad):
    with pytest.raises(Blocked):
        registered_router().propose(intent="trabalhar", text=bad, attachment_present=True)
