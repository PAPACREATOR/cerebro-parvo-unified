from __future__ import annotations

from dataclasses import dataclass


_ALLOWED_ACTIONS = frozenset({"APPROVE", "KEEP", "DELETE"})


def _validate_non_empty_string(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be a string")

    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be empty or whitespace-only")

    return value


def _validate_sha256(value: object, field_name: str) -> str:
    value = _validate_non_empty_string(value, field_name)

    if len(value) != 64:
        raise ValueError(f"{field_name} must contain exactly 64 characters")

    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(
            f"{field_name} must contain only lowercase hexadecimal characters"
        )

    return value


def _validate_action(value: object) -> str:
    value = _validate_non_empty_string(value, "action")

    if value not in _ALLOWED_ACTIONS:
        raise ValueError("action must be APPROVE, KEEP, or DELETE")

    return value


@dataclass(frozen=True, slots=True)
class HumanDecision:
    decision_id: str
    actor_id: str
    item_id: str
    version_sha256: str
    action: str

    def __post_init__(self) -> None:
        decision_id = _validate_non_empty_string(self.decision_id, "decision_id")
        actor_id = _validate_non_empty_string(self.actor_id, "actor_id")
        item_id = _validate_non_empty_string(self.item_id, "item_id")
        version_sha256 = _validate_sha256(self.version_sha256, "version_sha256")
        action = _validate_action(self.action)

        object.__setattr__(self, "decision_id", decision_id)
        object.__setattr__(self, "actor_id", actor_id)
        object.__setattr__(self, "item_id", item_id)
        object.__setattr__(self, "version_sha256", version_sha256)
        object.__setattr__(self, "action", action)


def promotion_allowed(
    decision: HumanDecision,
    item_id: str,
    version_sha256: str,
) -> bool:
    if type(decision) is not HumanDecision:
        raise TypeError("decision must be a HumanDecision")

    requested_item_id = _validate_non_empty_string(item_id, "item_id")
    requested_version_sha256 = _validate_sha256(version_sha256, "version_sha256")

    if requested_item_id != decision.item_id:
        raise ValueError("item_id does not match the decision")

    if requested_version_sha256 != decision.version_sha256:
        raise ValueError("version_sha256 does not match the decision")

    return decision.action == "APPROVE"
