from __future__ import annotations

from pathlib import Path
from typing import Any

from sibyl_memory_client import MemoryClient

from app.memory.storage import verify_memory_store
from app.services.memory_mapper import MuseMemory


class MemoryService:
    """Muse-level memory contract. Sibyl remains an implementation detail."""

    def write_memory(self, memory: MuseMemory) -> Any: ...
    def search_memory(self, query: str, *, user_id: str, limit: int = 20) -> list[Any]: ...
    def get_memory(self, memory_id: str, *, user_id: str) -> Any: ...
    def update_memory(self, memory_id: str, memory: MuseMemory, *, user_id: str) -> Any: ...
    def archive_memory(self, memory_id: str, *, user_id: str) -> Any: ...


class SibylMemoryService(MemoryService):
    """Muse memory boundary backed by the official Sibyl SDK."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path).expanduser()
        verify_memory_store(self._db_path.parent)
        self._client = MemoryClient.local(str(self._db_path))

    def check_ready(self) -> None:
        """Fail readiness if the configured Sibyl store cannot be opened."""
        verify_memory_store(self._db_path.parent)
        MemoryClient.local(str(self._db_path))

    @staticmethod
    def _tenant(client: MemoryClient, user_id: str) -> MemoryClient:
        client.set_tenant(user_id)
        return client

    def write_memory(self, memory: MuseMemory) -> Any:
        client = self._tenant(self._client, memory.user_id)
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
        return self._tenant(self._client, user_id).search(query, limit=limit)

    def get_memory(self, memory_id: str, *, user_id: str) -> Any:
        return self._tenant(self._client, user_id).get_entity(memory_id)

    def update_memory(self, memory_id: str, memory: MuseMemory, *, user_id: str) -> Any:
        if memory.user_id != user_id:
            raise ValueError("memory tenant does not match requested user")
        return self._tenant(self._client, user_id).set_entity(
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
        return self._tenant(self._client, user_id).archive_entity(memory_id)
