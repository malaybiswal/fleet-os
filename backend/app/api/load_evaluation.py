from fastapi import APIRouter
from app.seed.mock_loads import get_evaluated_mock_loads
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

@router.get("/mock-loads")
def get_mock_loads():
    return get_evaluated_mock_loads()