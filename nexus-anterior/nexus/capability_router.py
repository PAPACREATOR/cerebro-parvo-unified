"""Pure, fail-closed capability planner. Never imports or executes a tool.

The authoritative execution path remains Folha -> Host.start -> Store/Kernel
-> native sandbox/Writer Sandy -> Store.accept -> human Canonical gate.
This planner only selects a declared *existing* process from a closed registry.
"""
from dataclasses import dataclass
import re
import unicodedata

from nexus.contracts import Blocked


@dataclass(frozen=True, slots=True)
class Capability:
    process: str
    intent: str
    command: str
    tool: str
    requires_attachment: bool = True

    def __post_init__(self):
        if (not self.process or not self.tool or not self.command
                or not self.intent or type(self.requires_attachment) is not bool):
            raise ValueError("Capability contract incomplete")


# These are *registered candidates*, not a grant to execute them.
# Commands intentionally stay explicit while natural-language ambiguity is
# handled by the existing front door's clarification boundary.
BUILTIN_CAPABILITIES = (
    Capability("verify", "trabalhar", "verificar integridade de ficheiro", "verify_file"),
    Capability("interpret", "trabalhar", "interpretar documento", "interpret_file"),
    Capability("proofread", "trabalhar", "rever texto", "proofread_file"),
    Capability("convert_pdf", "trabalhar", "converter para pdf", "convert_pdf_file"),
    Capability("video", "trabalhar", "preparar plano de video", "video_plan_file"),
    Capability("podcast", "trabalhar", "preparar plano de podcast", "podcast_plan_file"),
    Capability("visual_podcast", "trabalhar", "preparar plano de podcast visual", "visual_podcast_plan_file"),
    Capability("book", "trabalhar", "exportar manuscrito para pdf", "book_file"),
    Capability("music", "trabalhar", "preparar plano de musica", "music_plan_file"),
    Capability("web", "web", "preparar plano de pesquisa web", "web_plan_file"),
)


def _normalise(text):
    if type(text) is not str or len(text) > 100_000:
        raise Blocked("Pedido inválido.")
    if any((ord(char) < 32 and char not in "\t\n\r") or 127 <= ord(char) < 160 for char in text):
        raise Blocked("Pedido inválido.")
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()


class CapabilityRouter:
    """Deterministic proposal-only router for N registered tools.

    Input must already have passed the Folha parser's intent/ambiguity gate.
    Registry uniqueness prevents priority from silently choosing a tool.
    """

    def __init__(self, capabilities):
        values = tuple(capabilities)
        if not values or not all(type(value) is Capability for value in values):
            raise ValueError("Registry must contain capabilities")
        keys = [(value.intent, _normalise(value.command)) for value in values]
        processes = [value.process for value in values]
        if len(keys) != len(set(keys)) or len(processes) != len(set(processes)):
            raise ValueError("Ambiguous or duplicate capability")
        self._capabilities = values

    def propose(self, *, intent, text, attachment_present):
        if type(intent) is not str or type(attachment_present) is not bool:
            raise Blocked("Pedido de seleção inválido.")
        normal = _normalise(text)
        if not normal:
            raise Blocked("Pedido vazio.")
        matches = [
            candidate for candidate in self._capabilities
            if candidate.intent == intent
            and _normalise(candidate.command) == normal
            and (not candidate.requires_attachment or attachment_present)
        ]
        if len(matches) != 1:
            raise Blocked("Operação desconhecida, incompleta ou ambígua.")
        return matches[0]


def registered_router():
    """Use only processes already present in the current signed contracts."""
    from nexus.adapters.runner import PROCESS_TO_TOOL, PROCESS_FILES
    from nexus.contracts import load_policy
    policy = load_policy()["processes"]
    if (set(PROCESS_TO_TOOL) != set(PROCESS_FILES) or set(policy) != set(PROCESS_TO_TOOL)
            or {c.process for c in BUILTIN_CAPABILITIES} != set(policy)
            or any(PROCESS_TO_TOOL[c.process] != c.tool for c in BUILTIN_CAPABILITIES)):
        raise Blocked("Registo de ferramentas incompatível com a política Nexus.")
    return CapabilityRouter(BUILTIN_CAPABILITIES)
