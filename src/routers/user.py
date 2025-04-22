import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ..logging.logging_config import setup_logging
from ..utils.authentication import CurrentUserDep
from ..models.user import UserDTO
from ..services import user
from ..utils.authentication import get_current_user


setup_logging()
debug_logger = logging.getLogger("debug")


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
async def get_user(
    auth_payload: CurrentUserDep, service: Annotated[user.UserService, Depends()]
) -> UserDTO:
    user_id = auth_payload["sub"]
    user = await service.get_user(user_id)
    if user:
        return user

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.post("/", dependencies=[Depends(get_current_user)])
async def create_user(user_data: UserDTO, service: Annotated[user.UserService, Depends()]) -> UserDTO:
    new_user = await service.create_user(user_data)
    return new_user
