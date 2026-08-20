from dataclasses import dataclass
from typing import Any, Protocol

@dataclass(frozen=True)
class Relationship: 
    from_entity: str
    to_entity: str
    type: str = "related_to"
    def model_dump(self, mode="python"): return {"from":self.from_entity,"to":self.to_entity,"type":self.type}

@dataclass(frozen=True)
class RelationshipGraph:
    extraction_run_id: str
    relationships: tuple[Relationship, ...]

class StructuredRelationshipClient(Protocol):
    async def extract_relationships(self, resolved: Any, schema: dict[str, Any]) -> Any: ...

async def extract_relationships(resolved: Any, *, client: StructuredRelationshipClient, extraction_run_id: str) -> RelationshipGraph:
    payload=await client.extract_relationships(resolved, {"extraction_run_id":extraction_run_id})
    raw=payload.get("relationships", []) if isinstance(payload,dict) else []
    return RelationshipGraph(extraction_run_id, tuple(x if isinstance(x,Relationship) else Relationship(str(x.get("from","")),str(x.get("to","")),str(x.get("type","related_to"))) for x in raw if isinstance(x,dict)))
