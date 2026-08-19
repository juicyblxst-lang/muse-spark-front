from __future__ import annotations

from pathlib import Path
from typing import Any

from sibyl_memory_client import MemoryClient

from app.services.memory_mapper import MuseMemory


class MemoryService:
    """Muse-level memory contract. Sibyl remains an implementation detail."""

    def write_memory(self, memory: MuseMemory) -> Any: ...
    def search_memory(self, query: str, *, user_id: str, limit: int = 20) -> list[Any]: ...
    def get_memory(self, memory_id: str, *, user_id: str) -> Any: ...
    def update_memory(self, memory_id: str, memory: MuseMemory, *, user_id: str) -> Any: ...
    def archive_memory(self, memory_id: str, *, user_id: str) -> Any: ...


class SibylMemoryService(MemoryService):
    """Thin adapter around the official local Sibyl SDK.

    The rest of Muse depends on MemoryService, not on Sibyl's API or storage engine.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._client = MemoryClient.local(str(Path(db_path).expanduser()))

    @staticmethod
    def _tenant(client: MemoryClient, user_id: str) -> MemoryClient:
        client.set_tenant(user_id)
        return client

    def write_memory(self, memory: MuseMemory) -> Any:
        client = self._tenant(self._client, memory.user_id)
        # Persist the mapped knowledge as an entity plus its full Muse payload.
        return client.set_entity(
            category="muse_memory",
            name=f"{memory.metadata.get('extraction_run_id', 'memory')}",
            body={
                "entities": memory.entities,
                "events": memory.events,
                "relationships": memory.relationships,
                "timelines": memory.timelines,
                "sources": [source.model_dump(mode="json") for source in memory.sources],
                "metadata": memory.metadata,
            },
        )

    def search_memory(self, query: str, *, user_id: str, limit: int = 20) -> list[Any]:
        client = self._tenant(self._client, user_id)
        return client.search(query, limit=limit)

    def get_memory(self, memory_id: str, *, user_id: str) -> Any:
        client = self._tenant(self._client, user_id)
        return client.get_entity(memory_id)

    def update_memory(self, memory_id: str, memory: MuseMemory, *, user_id: str) -> Any:
        if memory.user_id != user_id:
            raise ValueError("memory tenant does not match requested user")
        client = self._tenant(self._client, user_id)
        return client.set_entity(
            category="muse_memory",
            name=memory_id,
            body={
                "entities": memory.entities,
                "events": memory.events,
                "relationships": memory.relationships,
                "timelines": memory.timelines,
                "sources": [source.model_dump(mode="json") for source in memory.sources],
                "metadata": memory.metadata,
            },
        )

    def archive_memory(self, memory_id: str, *, user_id: str) -> Any:
        client = self._tenant(self._client, user_id)
        return client.archive_entity(memory_id)
