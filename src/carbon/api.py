"""Optional FastAPI adapter. Include router in the real backend during integration."""
from typing import Any, Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .engine import calculate_impact

router = APIRouter(prefix='/carbon', tags=['carbon'])


class ImpactRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    product_id: Literal['GP01', 'GP02', 'GP03', 'GP04']
    inputs: dict[str, Any]
    geography: str = 'UK'
    factor_year: int = Field(default=2026)


@router.post('/estimate')
def estimate(request: ImpactRequest):
    result = calculate_impact(request.product_id, request.inputs,
                              geography=request.geography, factor_year=request.factor_year)
    if result['status'] == 'invalid_input':
        raise HTTPException(status_code=422, detail=result)
    return result
