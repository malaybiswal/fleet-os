from fastapi import APIRouter

from app.schemas.load_evaluation import (
    LoadEvaluationRequest,
    LoadEvaluationResponse,
)
from app.services.load_evaluation_service import evaluate_load

router = APIRouter(prefix="/api/load-evaluation", tags=["load-evaluation"])


@router.post("/evaluate", response_model=LoadEvaluationResponse)
def evaluate_load_endpoint(
    request: LoadEvaluationRequest,
) -> LoadEvaluationResponse:
    return evaluate_load(request)
