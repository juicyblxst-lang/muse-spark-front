from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class ToolService(Protocol):
    def search_memory(self, query: str, *, user_id: str, limit: int = 20) -> list[Any]: ...
    def get_memory(self, memory_id: str, *, user_id: str) -> Any: ...


class ToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: str = Field(min_length=1)


class SearchMemoryInput(ToolInput):
    query: str = Field(min_length=1)
    limit: int = Field(default=20, ge=1, le=100)


class MemoryInput(ToolInput):
    memory_id: str = Field(min_length=1, max_length=256)


class EntityInput(ToolInput):
    entity_id: str = Field(min_length=1, max_length=256)


class RelationshipInput(ToolInput):
    entity_id: str = Field(min_length=1, max_length=256)
    limit: int = Field(default=50, ge=1, le=100)


class TimelineInput(ToolInput):
    entity_id: str = Field(min_length=1, max_length=256)


class SourceInput(ToolInput):
    source_id: str = Field(min_length=1, max_length=256)


class AbandonedIdeasInput(ToolInput):
    limit: int = Field(default=20, ge=1, le=100)


class AgentTool(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    name: str
    description: str
    input_schema: type[BaseModel]
    handler: Any


def _require_user(user_id: str) -> str:
    if not user_id.strip():
        raise ValueError("user_id is required")
    return user_id


def _require_owner(record: Any, user_id: str) -> Any:
    """Defense-in-depth tenant check for service results."""
    if isinstance(record, dict):
        owner = record.get("user_id") or record.get("tenant_id")
        if owner is not None and owner != user_id:
            raise PermissionError("record does not belong to requested user")
    return record


def search_memory(service: ToolService, args: SearchMemoryInput) -> list[Any]:
    user_id = _require_user(args.user_id)
    return [_require_owner(v, user_id) for v in service.search_memory(args.query.strip(), user_id=user_id, limit=args.limit)]


def get_memory(service: ToolService, args: MemoryInput) -> Any:
    return _require_owner(service.get_memory(args.memory_id, user_id=_require_user(args.user_id)), args.user_id)


def _unsupported(name: str) -> None:
    raise NotImplementedError(f"{name} requires a Muse service adapter")


def get_entity(service: ToolService, args: EntityInput) -> Any:
    _unsupported("get_entity")


def get_relationships(service: ToolService, args: RelationshipInput) -> Any:
    _unsupported("get_relationships")


def get_timeline(service: ToolService, args: TimelineInput) -> Any:
    _unsupported("get_timeline")


def get_source(service: ToolService, args: SourceInput) -> Any:
    _unsupported("get_source")


def find_abandoned_ideas(service: ToolService, args: AbandonedIdeasInput) -> Any:
    _unsupported("find_abandoned_ideas")


def build_muse_tools(service: ToolService) -> tuple[AgentTool, ...]:
    """Return the only tools exposed to the agent. No SQL/filesystem tools exist here."""
    return (
        AgentTool(name="search_memory", description="Search the user's Muse memory.", input_schema=SearchMemoryInput, handler=lambda a: search_memory(service, a)),
        AgentTool(name="get_memory", description="Get one authorized memory.", input_schema=MemoryInput, handler=lambda a: get_memory(service, a)),
        AgentTool(name="get_entity", description="Get one authorized entity.", input_schema=EntityInput, handler=lambda a: get_entity(service, a)),
        AgentTool(name="get_relationships", description="Get relationships for an authorized entity.", input_schema=RelationshipInput, handler=lambda a: get_relationships(service, a)),
        AgentTool(name="get_timeline", description="Get timeline information for an authorized entity.", input_schema=TimelineInput, handler=lambda a: get_timeline(service, a)),
        AgentTool(name="get_source", description="Get an authorized source reference.", input_schema=SourceInput, handler=lambda a: get_source(service, a)),
        AgentTool(name="find_abandoned_ideas", description="Find abandoned ideas belonging to the current user.", input_schema=AbandonedIdeasInput, handler=lambda a: find_abandoned_ideas(service, a)),
    )
