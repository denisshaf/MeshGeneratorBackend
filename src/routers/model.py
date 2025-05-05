from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query

from ..services.model import ModelService
from ..utils.authentication import get_current_user

router = APIRouter(
    prefix="/users/me/models", tags=["Models"], dependencies=[Depends(get_current_user)]
)


@router.get("/urls")
async def get_batch(
    id: Annotated[list[int], Query()], model_service: Annotated[ModelService, Depends()]
) -> dict[int, str]:
    urls = await model_service.get_batch_urls(id)
    return urls


@router.get("/{model_id}/url")
async def get_model(
    model_id: int, model_service: Annotated[ModelService, Depends()]
) -> str:
    url = await model_service.get_url_by_id(model_id)
    return url
