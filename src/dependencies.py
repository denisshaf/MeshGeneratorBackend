from typing import Annotated

from fastapi import Depends
from fastapi.exceptions import HTTPException

from .services.user import UserService
from .utils.authentication import CurrentUserDep


# TODO: need to return more helpful error message when user doesn't exist or chat doesn't exist.
async def validate_chat_id(
    chat_id: int,
    user: CurrentUserDep,
    user_service: Annotated[UserService, Depends()],
) -> None:
    user_auth_id = user["sub"]
    is_chat_owner = await user_service.is_chat_owner(user_auth_id, chat_id)

    if not is_chat_owner:
        raise HTTPException(
            status_code=403, detail="You are not the owner of this chat"
        )
