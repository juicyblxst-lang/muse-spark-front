from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.services.feedback import CorrectionService, CorrectionType, InMemoryCorrectionStore, UserCorrection

router = APIRouter(prefix="/feedback", tags=["feedback"])
_store = InMemoryCorrectionStore()
_service = CorrectionService(_store)


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)
    target_object: dict[str, Any]
    correction_type: CorrectionType
    original_interpretation: Any
    corrected_interpretation: Any


class FeedbackResponse(BaseModel):
    correction_id: str
    user_id: str
    target_object: dict[str, Any]
    correction_type: CorrectionType
    original_interpretation: Any
    corrected_interpretation: Any
    timestamp: str


def get_correction_service() -> CorrectionService:
    return _service


@router.post("", response_model=FeedbackResponse, status_code=201)
def create_feedback(
    payload: FeedbackRequest,
    service: CorrectionService = Depends(get_correction_service),
) -> FeedbackResponse:
    correction = service.record(
        correction_id=str(uuid4()),
        user_id=payload.user_id,
        target_object=payload.target_object,
        correction_type=payload.correction_type,
        original_interpretation=payload.original_interpretation,
        corrected_interpretation=payload.corrected_interpretation,
    )
    return FeedbackResponse(
        correction_id=correction.correction_id,
        user_id=correction.user_id,
        target_object=correction.target_object,
        correction_type=correction.correction_type,
        original_interpretation=correction.original_interpretation,
        corrected_interpretation=correction.corrected_interpretation,
        timestamp=correction.timestamp.isoformat(),
    )
