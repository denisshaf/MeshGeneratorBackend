from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query

from ..services.model import ModelService
from ..repository.model import ModelDTO
from ..utils.authentication import get_current_user, CurrentUserDep 

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
async def get_model_url(
    model_id: int, model_service: Annotated[ModelService, Depends()]
) -> str:
    url = await model_service.get_url_by_id(model_id)
    return url


@router.patch("/{model_id}/add-to-favorites")
async def add_to_favorites(
    model_id: int,
    user: CurrentUserDep,
    model_service: Annotated[ModelService, Depends()],
) -> None:
    user_auth_id = user["sub"]
    await model_service.add_to_favorites(user_auth_id, model_id)


@router.get("/favorites")
async def get_favorite_models(
    user: CurrentUserDep,
    model_service: Annotated[ModelService, Depends()],
) -> list[ModelDTO]:
    user_auth_id = user["sub"]
    models = await model_service.get_favorite_models(user_auth_id)
    return models


@router.patch("/{model_id}/remove-from-favorites")
async def remove_from_favorites(
    model_id: int,
    model_service: Annotated[ModelService, Depends()],
) -> None:
    await model_service.remove_from_favorites(model_id)
