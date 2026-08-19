from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence
from uuid import uuid4

from app.services.entity_resolution import EntityCandidate, ResolvedExtraction, resolve_extraction
from app.services.extraction import ExtractionResult, StructuredLLMClient, extract_document
from app.services.ingestion import DoclingIngestionService, IngestedDocument
from app.services.memory_mapper import Confidence, MemoryMapper, MuseMemory, ProvenancedKnowledge, SourceReference
from app.services.normalization import MuseDocument, normalize_document
from app.services.provenance import ProvenanceRecord, create_provenance_record, validate_source_provenance
from app.services.relationships import RelationshipGraph, StructuredRelationshipClient, extract_relationships
from app.services.temporal_analysis import StructuredTemporalClient, TemporalAnalysis, analyze_temporal


class EntityResolverClient:
    """Adapter contract used by the full pipeline; persistence stays outside intelligence."""

    async def candidates(
        self,
        *,
        user_id: str,
        mention: str,
        entity_type: str,
    ) -> Sequence[EntityCandidate]:
        raise NotImplementedError


class MemoryWriter:
    def write_memory(self, memory: MuseMemory) -> Any:
        raise NotImplementedError


@dataclass(frozen=True)
class PipelineDependencies:
    extraction: StructuredLLMClient
    resolver: EntityResolverClient
    relationships: StructuredRelationshipClient
    temporal: StructuredTemporalClient
    memory: MemoryWriter
    ingestion: DoclingIngestionService


@dataclass(frozen=True)
class PipelineRun:
    extraction_run_id: str
    ingested: IngestedDocument
    document: MuseDocument
    extraction: ExtractionResult
    resolution: ResolvedExtraction
    relationships: RelationshipGraph
    temporal: TemporalAnalysis
    provenance: tuple[ProvenanceRecord, ...]
    knowledge: ProvenancedKnowledge
    memory: MuseMemory
    memory_id: Any


class MuseComponentPipeline:
    """Connect the already-tested intelligence stages without owning external persistence."""

    def __init__(self, dependencies: PipelineDependencies) -> None:
        self.dependencies = dependencies

    async def run(
        self,
        source_path: str,
        *,
        user_id: str,
        document_id: str,
        document_version: str = "1",
        extraction_run_id: str | None = None,
    ) -> PipelineRun:
        run_id = extraction_run_id or str(uuid4())

        ingested = self.dependencies.ingestion.ingest(source_path)
        document = normalize_document(ingested)
        extraction = await extract_document(document, self.dependencies.extraction)
        resolution = await resolve_extraction(
            extraction,
            user_id=user_id,
            resolver=self.dependencies.resolver,
        )
        relationships = await extract_relationships(
            resolution,
            client=self.dependencies.relationships,
            extraction_run_id=run_id,
        )
        temporal = await analyze_temporal(
            relationships,
            client=self.dependencies.temporal,
            extraction_run_id=run_id,
        )

        provenance = tuple(self._build_provenance(
            document,
            document_id=document_id,
            document_version=document_version,
            extraction_run_id=run_id,
        ))
        validate_source_provenance(provenance)

        knowledge = self._build_knowledge(
            user_id=user_id,
            extraction=extraction,
            resolution=resolution,
            relationships=relationships,
            temporal=temporal,
            provenance=provenance,
            extraction_run_id=run_id,
        )
        memory = MemoryMapper().map(knowledge)
        memory_id = self.dependencies.memory.write_memory(memory)

        return PipelineRun(
            extraction_run_id=run_id,
            ingested=ingested,
            document=document,
            extraction=extraction,
            resolution=resolution,
            relationships=relationships,
            temporal=temporal,
            provenance=provenance,
            knowledge=knowledge,
            memory=memory,
            memory_id=memory_id,
        )

    @staticmethod
    def _build_provenance(
        document: MuseDocument,
        *,
        document_id: str,
        document_version: str,
        extraction_run_id: str,
    ) -> list[ProvenanceRecord]:
        records: list[ProvenanceRecord] = []
        for index, block in enumerate(document.blocks, start=1):
            if not block.text.strip():
                continue
            records.append(
                create_provenance_record(
                    document_id=document_id,
                    document_version=document_version,
                    page=block.page,
                    block_id=str(index),
                    source_text=block.text,
                    source_location=f"page {block.page}, block {index}" if block.page else f"block {index}",
                    extraction_run_id=extraction_run_id,
                    model="component-pipeline",
                )
            )
        return records

    @staticmethod
    def _build_knowledge(
        *,
        user_id: str,
        extraction: ExtractionResult,
        resolution: ResolvedExtraction,
        relationships: RelationshipGraph,
        temporal: TemporalAnalysis,
        provenance: Sequence[ProvenanceRecord],
        extraction_run_id: str,
    ) -> ProvenancedKnowledge:
        resolution_by_mention = {mention.mention: mention for mention in resolution.mentions}
        entities: list[dict[str, Any]] = []
        for entity_type, items in (
            ("person", extraction.people),
            ("organization", extraction.organizations),
            ("project", extraction.projects),
            ("creative_work", extraction.creative_works),
            ("concept", extraction.concepts),
        ):
            for item in items:
                resolved = resolution_by_mention[item.name]
                entities.append({
                    "name": item.name,
                    "type": entity_type,
                    "description": item.description,
                    "evidence": list(item.evidence),
                    "resolution_status": resolved.status.value,
                    "entity_id": resolved.entity_id,
                    "candidate_ids": list(resolved.candidate_ids),
                    "resolution_confidence": resolved.confidence,
                })

        events = [
            {
                "id": event.temporal_event_id,
                "entity_id": event.referenced_entity.entity_id,
                "mention": event.referenced_entity.mention,
                "precision": event.precision.value,
                "normalized_start": event.normalized_start,
                "normalized_end": event.normalized_end,
                "original_expression": event.original_expression,
                "source_evidence": list(event.source_evidence),
                "source_location": event.source_location,
                "relation": event.relation.value,
                "relation_target": event.relation_target.model_dump(mode="json") if event.relation_target else None,
                "uncertainty": event.uncertainty,
                "duration": event.duration,
            }
            for event in temporal.events
        ]
        relationship_payload = [relationship.model_dump(mode="json") for relationship in relationships.relationships]
        timeline_payload = [event.model_dump(mode="json") for event in temporal.events]

        return ProvenancedKnowledge(
            user_id=user_id,
            entities=entities,
            events=events,
            relationships=relationship_payload,
            timelines=timeline_payload,
            source_references=[
                SourceReference(
                    provenance_id=record.provenance_id,
                    document_id=record.document_id,
                    document_version=record.document_version,
                    source_location=record.source_location,
                )
                for record in provenance
            ],
            confidence=Confidence(value=0.0, status="pipeline-complete") if not entities else Confidence(
                value=min(item["resolution_confidence"] for item in entities),
                status="pipeline-complete",
            ),
            extraction_run_id=extraction_run_id,
        )
