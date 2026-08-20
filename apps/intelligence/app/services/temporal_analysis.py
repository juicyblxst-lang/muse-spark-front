from dataclasses import dataclass
from typing import Any, Protocol

@dataclass(frozen=True)
class TemporalEvent:
    label: str
    date: str | None = None
    def model_dump(self, mode="python"): return {"label":self.label,"date":self.date}

@dataclass(frozen=True)
class TemporalAnalysis:
    extraction_run_id: str
    events: tuple[TemporalEvent, ...]

class StructuredTemporalClient(Protocol):
    async def analyze_temporal(self, relationships: Any, schema: dict[str, Any]) -> Any: ...

async def analyze_temporal(relationships: Any, *, client: StructuredTemporalClient, extraction_run_id: str) -> TemporalAnalysis:
    payload=await client.analyze_temporal(relationships, {"extraction_run_id":extraction_run_id})
    raw=payload.get("events", []) if isinstance(payload,dict) else []
    return TemporalAnalysis(extraction_run_id, tuple(x if isinstance(x,TemporalEvent) else TemporalEvent(str(x.get("label","")),x.get("date")) for x in raw if isinstance(x,dict)))
