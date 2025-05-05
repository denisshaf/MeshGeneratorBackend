from typing import Annotated

from fastapi import Depends

from ..repository.model import AsyncModelRepository, AsyncS3ModelRepository


class ModelService:
    def __init__(
        self,
        model_repository: Annotated[
            AsyncModelRepository, Depends(AsyncS3ModelRepository)
        ],
    ):
        self._model_repository = model_repository

    async def get_url_by_id(self, model_id: int) -> str:
        return await self._model_repository.get_url(model_id)

    async def get_batch_urls(self, model_ids: list[int]) -> dict[int, str]:
        return await self._model_repository.get_batch_urls(model_ids)
