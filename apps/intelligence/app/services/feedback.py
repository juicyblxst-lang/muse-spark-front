from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol


class CorrectionType(str, Enum):
    ENTITY_TYPE = "entity_type"
    ENTITY_IDENTITY = "entity_identity"
    RELATIONSHIP = "relationship"
    TEMPORAL = "temporal"
    SOURCE_INTERPRETATION = "source_interpretation"


@dataclass(frozen=True)
class UserCorrection:
    correction_id: str
    user_id: str
    target_object: dict[str, Any]
    correction_type: CorrectionType
    original_interpretation: Any
    corrected_interpretation: Any
    timestamp: datetime


class CorrectionStore(Protocol):
    def save(self, correction: UserCorrection) -> UserCorrection: ...
    def list_for_user(self, user_id: str) -> list[UserCorrection]: ...


class InMemoryCorrectionStore:
    """Development/test store. Production storage is supplied by the API layer."""

    def __init__(self) -> None:
        self._items: list[UserCorrection] = []

    def save(self, correction: UserCorrection) -> UserCorrection:
        self._items.append(correction)
        return correction

    def list_for_user(self, user_id: str) -> list[UserCorrection]:
        return [item for item in self._items if item.user_id == user_id]


class CorrectionService:
    def __init__(self, store: CorrectionStore) -> None:
        self._store = store

    def record(
        self,
        *,
        correction_id: str,
        user_id: str,
        target_object: dict[str, Any],
        correction_type: CorrectionType,
        original_interpretation: Any,
        corrected_interpretation: Any,
    ) -> UserCorrection:
        if not user_id.strip():
            raise ValueError("user_id is required")
        if not target_object:
            raise ValueError("target_object is required")
        if original_interpretation is None:
            raise ValueError("original_interpretation is required")
        if corrected_interpretation is None:
            raise ValueError("corrected_interpretation is required")

        return self._store.save(
            UserCorrection(
                correction_id=correction_id,
                user_id=user_id,
                target_object=dict(target_object),
                correction_type=correction_type,
                original_interpretation=original_interpretation,
                corrected_interpretation=corrected_interpretation,
                timestamp=datetime.now(timezone.utc),
            )
        )

    def get_for_resolution(self, user_id: str) -> list[UserCorrection]:
        if not user_id.strip():
            raise ValueError("user_id is required")
        return self._store.list_for_user(user_id)
