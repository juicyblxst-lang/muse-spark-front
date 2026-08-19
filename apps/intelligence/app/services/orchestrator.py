from dataclasses import dataclass
from enum import StrEnum
from typing import Awaitable, Callable


class ProcessingStage(StrEnum):
    INGESTION = "ingestion"
    NORMALIZATION = "normalization"
    EXTRACTION = "extraction"
    ENTITY_RESOLUTION = "entity_resolution"
    RELATIONSHIP_BUILDING = "relationship_building"
    TIMELINE_BUILDING = "timeline_building"
    FINALIZATION = "finalization"


@dataclass(frozen=True)
class StageResult:
    stage: ProcessingStage
    status: str = "complete"
    detail: dict | None = None


@dataclass(frozen=True)
class PipelineResult:
    status: str
    stages: list[StageResult]


StageHandler = Callable[[], Awaitable[StageResult]]


class ProcessingOrchestrator:
    """Controls pipeline order and stage state; it does not perform intelligence."""

    DEFAULT_STAGES = (
        ProcessingStage.INGESTION,
        ProcessingStage.NORMALIZATION,
        ProcessingStage.EXTRACTION,
        ProcessingStage.ENTITY_RESOLUTION,
        ProcessingStage.RELATIONSHIP_BUILDING,
        ProcessingStage.TIMELINE_BUILDING,
        ProcessingStage.FINALIZATION,
    )

    def __init__(self, handlers: dict[ProcessingStage, StageHandler] | None = None) -> None:
        self.handlers = handlers or {}

    async def run(self) -> PipelineResult:
        results: list[StageResult] = []
        for stage in self.DEFAULT_STAGES:
            handler = self.handlers.get(stage)
            if handler is None:
                results.append(StageResult(stage=stage, detail={"state": "pending"}))
                continue
            result = await handler()
            if result.stage != stage:
                raise ValueError(f"Handler returned {result.stage}, expected {stage}")
            results.append(result)
            if result.status == "failed":
                return PipelineResult(status="failed", stages=results)
        return PipelineResult(status="complete", stages=results)


orchestrator = ProcessingOrchestrator()
