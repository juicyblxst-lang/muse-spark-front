from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Protocol
from uuid import uuid4

from app.services.entity_resolution import EntityResolver, ResolvedExtraction, resolve_extraction
from app.services.extraction import ExtractionResult, StructuredLLMClient, extract_document
from app.services.ingestion import DoclingIngestionService, IngestedDocument
from app.services.memory_mapper import (
    Confidence,
    MemoryMapper,
    MuseMemory,
    ProvenancedKnowledge,
    SibylMemoryWriter,
    SourceReference,
)
from app.services.normalization import MuseDocument, normalize_document
from app.services.processing_state import ProcessingStage
from app.services.provenance import ProvenanceRecord, ProvenanceStore, create_provenance_record
from app.services.relationships import RelationshipGraph, StructuredRelationshipClient, extract_relationships
from app.services.temporal_analysis import TemporalAnalysis, StructuredTemporalClient, analyze_temporal


class PipelineDocumentIngestor(Protocol):
    def ingest(self, source_path: str | Path) -> IngestedDocument: ...


StageCallback = Callable[[ProcessingStage, int], Awaitable[None]]


@dataclass(frozen=True)
class PipelineRun:
    ingestion: IngestedDocument
    document: MuseDocument
    extraction: ExtractionResult
    resolution: ResolvedExtraction
    relationships: RelationshipGraph
    temporal: TemporalAnalysis
    provenance: tuple[ProvenanceRecord, ...]
    knowledge: ProvenancedKnowledge
    memory: MuseMemory
    memory_id: Any
    extraction_run_id: str


class MuseComponentPipeline:
    """Connects the existing intelligence contracts without owning external persistence."""

    def __init__(
        self,
        *,
        ingestion: PipelineDocumentIngestor,
        extraction_client: StructuredLLMClient,
        resolver: EntityResolver,
        relationship_client: StructuredRelationshipClient,
        temporal_client: StructuredTemporalClient,
        memory_writer: SibylMemoryWriter,
        provenance_store: ProvenanceStore | None = None,
        model: str = "muse-pipeline",
    ) -> None:
        self.ingestion = ingestion
        self.extraction_client = extraction_client
        self.resolver = resolver
        self.relationship_client = relationship_client
        self.temporal_client = temporal_client
        self.memory_writer = memory_writer
        self.provenance_store = provenance_store or ProvenanceStore()
        self.model = model

    async def run(
        self,
        source_path: str | Path,
        *,
        user_id: str,
        document_id: str,
        document_version: str = "1",
        extraction_run_id: str | None = None,
        stage_callback: StageCallback | None = None,
    ) -> PipelineRun:
        run_id = extraction_run_id or str(uuid4())

        async def stage(name: ProcessingStage, progress: int) -> None:
            if stage_callback is not None:
                await stage_callback(name, progress)

        await stage(ProcessingStage.INGESTION, 10)
        ingested = self.ingestion.ingest(source_path)

        await stage(ProcessingStage.NORMALIZATION, 20)
        document = normalize_document(ingested)

        await stage(ProcessingStage.EXTRACTION, 35)
        extraction = await extract_document(document, self.extraction_client)

        await stage(ProcessingStage.ENTITY_RESOLUTION, 50)
        resolution = await resolve_extraction(
            extraction,
            user_id=user_id,
            resolver=self.resolver,
        )

        await stage(ProcessingStage.RELATIONSHIP_BUILDING, 65)
        relationships = await extract_relationships(
            resolution,
            client=self.relationship_client,
            extraction_run_id=run_id,
        )

        await stage(ProcessingStage.TIMELINE_BUILDING, 78)
        temporal = await analyze_temporal(
            relationships,
            client=self.temporal_client,
            extraction_run_id=run_id,
        )

        await stage(ProcessingStage.FINALIZATION, 90)
        provenance = tuple(self._build_provenance(document, document_id, document_version, run_id))
        knowledge = self._build_knowledge(
            user_id=user_id,
            extraction_run_id=run_id,
            resolution=resolution,
            relationships=relationships,
            temporal=temporal,
            provenance=provenance,
        )
        memory = MemoryMapper().map(knowledge)
        memory_id = MemoryMapper().write(knowledge, self.memory_writer)
        await stage(ProcessingStage.FINALIZATION, 100)

        return PipelineRun(
            ingestion=ingested,
            document=document,
            extraction=extraction,
            resolution=resolution,
            relationships=relationships,
            temporal=temporal,
            provenance=provenance,
            knowledge=knowledge,
            memory=memory,
            memory_id=memory_id,
            extraction_run_id=run_id,
        )

    def _build_provenance(
        self,
        document: MuseDocument,
        document_id: str,
        document_version: str,
        extraction_run_id: str,
    ) -> list[ProvenanceRecord]:
        records: list[ProvenanceRecord] = []
        for index, block in enumerate(document.blocks, start=1):
            if not block.text.strip():
                continue
            record = create_provenance_record(
                document_id=document_id,
                document_version=document_version,
                page=block.page,
                block_id=str(index),
                source_text=block.text,
                source_location=f"page {block.page}, block {index}" if block.page else f"block {index}",
                extraction_run_id=extraction_run_id,
                model=self.model,
            )
            self.provenance_store.add(record)
            records.append(record)
        return records

    @staticmethod
    def _build_knowledge(
        *,
        user_id: str,
        extraction_run_id: str,
        resolution: ResolvedExtraction,
        relationships: RelationshipGraph,
        temporal: TemporalAnalysis,
        provenance: tuple[ProvenanceRecord, ...],
    ) -> ProvenancedKnowledge:
        entities = [
            {
                "mention": mention.mention,
                "type": mention.entity_type,
                "resolution_status": mention.status.value,
                "entity_id": mention.entity_id,
                "candidate_ids": list(mention.candidate_ids),
                "confidence": mention.confidence,
                "evidence": list(mention.evidence),
            }
            for mention in resolution.mentions
        ]
        relationship_payload = [relationship.model_dump(mode="json") for relationship in relationships.relationships]
        timeline_payload = [event.model_dump(mode="json") for event in temporal.events]
        source_refs = [
            SourceReference(
                provenance_id=record.provenance_id,
                document_id=record.document_id,
                document_version=record.document_version,
                source_location=record.source_location,
            )
            for record in provenance
        ]
        return ProvenancedKnowledge(
            user_id=user_id,
            entities=entities,
            events=timeline_payload,
            relationships=relationship_payload,
            timelines=timeline_payload,
            source_references=source_refs,
            confidence=Confidence(value=1.0, status="pipeline-validated"),
            extraction_run_id=extraction_run_id,
        )


class DefaultPipelineProvider:
    """Small composition-root helper; all external services remain injected."""

    def __init__(self, factory: Callable[[str], MuseComponentPipeline]) -> None:
        self.factory = factory

    def build(self, user_id: str) -> MuseComponentPipeline:
        return self.factory(user_id)
