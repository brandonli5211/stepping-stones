"""Domain entity for the starting non-coaching app_meta record."""

from __future__ import annotations

from dataclasses import dataclass


class AppMetaValidationError(ValueError):
    """Raised when key or value rules are not met."""


@dataclass(frozen=True)
class AppMeta:
    """Pure starting-record rules. No framework or ORM imports."""

    key: str
    value: str
    id: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.key, str) or not self.key.strip():
            raise AppMetaValidationError("key is required")
        if not isinstance(self.value, str) or not self.value.strip():
            raise AppMetaValidationError("value is required")


def create_app_meta(*, key: str, value: str, id: int | None = None) -> AppMeta:
    """Build a validated AppMeta entity."""
    return AppMeta(key=key, value=value, id=id)
