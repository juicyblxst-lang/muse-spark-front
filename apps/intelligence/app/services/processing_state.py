from enum import Enum

class ProcessingStage(str, Enum):
    INGESTION = "ingestion"
    NORMALIZATION = "normalization"
    EXTRACTION = "extraction"
    ENTITY_RESOLUTION = "entity_resolution"
    RELATIONSHIP_BUILDING = "relationship_building"
    TIMELINE_BUILDING = "timeline_building"
    FINALIZATION = "finalization"
