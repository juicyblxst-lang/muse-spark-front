from dataclasses import dataclass
from typing import Any, Protocol

class StructuredLLMClient(Protocol):
    async def extract(self, document: Any, schema: dict[str, Any]) -> Any: ...

@dataclass(frozen=True)
class ExtractionResult:
    document: Any
    payload: dict[str, Any]

async def extract_document(document: Any, client: StructuredLLMClient) -> ExtractionResult:
    payload = await client.extract(document, {"type":"object"})
    return ExtractionResult(document, payload if isinstance(payload, dict) else {})
