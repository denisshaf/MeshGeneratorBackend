from typing import Annotated

from fastapi import Depends

from ..repository.model import AsyncModelRepository, AsyncS3ModelRepository, ModelDTO
from ..repository.user import AsyncUserRepository


class ModelService:
    def __init__(
        self,
        model_repository: Annotated[
            AsyncModelRepository, Depends(AsyncS3ModelRepository)
        ],
        user_repository: Annotated[AsyncUserRepository, Depends()],
    ):
        self._model_repository = model_repository
        self._user_repository = user_repository

    async def get_url_by_id(self, model_id: int) -> str:
        return await self._model_repository.get_url(model_id)

    async def get_batch_urls(self, model_ids: list[int]) -> dict[int, str]:
        return await self._model_repository.get_batch_urls(model_ids)

    async def add_to_favorites(self, auth_id: str, model_id: int) -> None:
        user = await self._user_repository.get_by_auth_id(auth_id)

        if not user:
            raise ValueError("User not found")

        assert user.id

        await self._model_repository.set_user_id(user.id, model_id)

    async def remove_from_favorites(self, model_id: int) -> None:
        await self._model_repository.set_user_id(None, model_id)

    async def get_favorite_models(self, auth_id: str) -> list[ModelDTO]:
        user = await self._user_repository.get_by_auth_id(auth_id)

        if not user:
            raise ValueError("User not found")

        assert user.id

        models = await self._model_repository.get_having_user_id(user.id)
        return models