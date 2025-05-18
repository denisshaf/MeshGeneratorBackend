import logging
import uuid
from abc import ABC, abstractmethod
from typing import Annotated, cast

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db_session
from ..models.model import ModelDAO, ModelDTO

logger = logging.getLogger("app")
debug_logger = logging.getLogger("debug")


load_dotenv()


class AsyncModelRepository(ABC):
    @abstractmethod
    async def save(self, message_id: int, content: str) -> ModelDTO: ...
    @abstractmethod
    async def get_url(self, model_id: int) -> str: ...
    @abstractmethod
    async def get_batch_urls(self, model_ids: list[int]) -> dict[int, str]: ...
    @abstractmethod
    async def aclose(self) -> None: ...

    def __init__(self, db_session: Annotated[AsyncSession, Depends(get_db_session)]):
        self._db_session = db_session

    async def set_user_id(self, user_id: int | None, model_id: int) -> None:
        query = (
            update(ModelDAO)
            .filter(ModelDAO.id == model_id)
            .values(user_id=user_id)
        )
        result = await self._db_session.execute(query)

        await self._db_session.commit()

        if not result.rowcount:
            raise ValueError(f"Model with id {model_id} not found")

    async def get_having_user_id(self, user_id: int) -> list[ModelDTO]:
        query = select(ModelDAO).filter(ModelDAO.user_id == user_id)
        result = await self._db_session.execute(query)
        model_daos = result.scalars().all()
        
        models = [ModelDTO.model_validate(model_dao) for model_dao in model_daos]
        return models


class AsyncS3ModelRepository(AsyncModelRepository):
    def __init__(
        self, db_session: Annotated[AsyncSession, Depends(get_db_session)]
    ) -> None:
        super().__init__(db_session)

        self._s3 = boto3.client("s3")
        self._bucket_name_prefix = "obj-storage"
        self._bucket_name = self._get_or_create_bucket(self._bucket_name_prefix)

    async def aclose(self) -> None:
        await self._db_session.close()
        self._s3.close()

    def _get_or_create_bucket(self, prefix: str) -> str:
        buckets = self._s3.list_buckets()["Buckets"]

        for bucket in buckets:
            if bucket["Name"].startswith(prefix):
                return cast(str, bucket["Name"])

        bucket_name = f"{prefix}-{uuid.uuid4()}"
        bucket_name = bucket_name.lower()

        try:
            self._s3.create_bucket(Bucket=bucket_name)
            return bucket_name
        except ClientError as e:
            logger.error(f"Failed to create bucket {bucket_name}: {e}")
            raise

    @staticmethod
    def _get_s3_url(bucket_name: str, object_key: str) -> str:
        return f"s3://{bucket_name}/{object_key}"

    @staticmethod
    def _get_bucket_and_object_keys(s3_path: str) -> tuple[str, str]:
        if not s3_path.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI: {s3_path}")

        path = s3_path[5:]

        parts = path.split("/", 1)
        bucket = parts[0]

        key = parts[1] if len(parts) > 1 else ""

        return bucket, key

    def _save_content_to_s3(self, content: str) -> str:
        bucket_name = self._bucket_name
        object_key = f"{uuid.uuid4()}.obj"

        try:
            self._s3.put_object(Body=content, Bucket=bucket_name, Key=object_key)
            s3_url = self._get_s3_url(bucket_name, object_key)
        except ClientError as e:
            logger.error(f"Failed to upload the content to the bucket: {e}")
            raise

        return s3_url

    async def save(self, message_id: int, content: str) -> ModelDTO:  # type: ignore
        try:
            s3_url = self._save_content_to_s3(content)

            new_model = ModelDAO(
                storage_path=s3_url,
                message_id=message_id,
            )
            self._db_session.add(new_model)
            await self._db_session.commit()
            await self._db_session.refresh(new_model)
        except BaseException as e:
            logger.error(f"Failed to save the model to the database: {e}")
            await self._db_session.rollback()
            raise

        return ModelDTO.model_validate(new_model)

    def _generate_presigned_url(self, bucket_name: str, object_key: str) -> str:
        try:
            response = self._s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": object_key},
                ExpiresIn=3600,  # URL expires in 1 hour
            )
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise

        return cast(str, response)

    async def get_url(self, model_id: int) -> str:
        query = select(ModelDAO).filter(ModelDAO.id == model_id)
        result = await self._db_session.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Model with id {model_id} not found")

        assert model.storage_path

        bucket_name, object_key = self._get_bucket_and_object_keys(model.storage_path)

        presigned_url = self._generate_presigned_url(bucket_name, object_key)

        return presigned_url

    async def get_batch_urls(self, model_ids: list[int]) -> dict[int, str]:
        query = select(ModelDAO).filter(ModelDAO.id.in_(model_ids))
        result = await self._db_session.execute(query)
        models = result.scalars().all()

        found_ids = {model.id for model in models}
        missing_ids = set(model_ids) - found_ids
        if missing_ids:
            raise ValueError(f"Models with ids {missing_ids} not found")

        id_to_url = {}
        for model in models:
            assert model.storage_path
            bucket_name, object_key = self._get_bucket_and_object_keys(
                model.storage_path
            )
            presigned_url = self._generate_presigned_url(bucket_name, object_key)
            id_to_url[model.id] = presigned_url

        return id_to_url
