import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ..config.logging_config import setup_logging
from ..dependencies import CurrentUserDep
from ..models.user import UserDTO
from ..services.user import UserService
from ..utils.authentication import get_current_user

setup_logging()
debug_logger = logging.getLogger("debug")

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
async def get_user(
    auth_payload: CurrentUserDep, service: Annotated[UserService, Depends()]
):
    user_id = auth_payload["sub"]
    user = await service.get_user(user_id)
    if user:
        return user

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.post("/", dependencies=[Depends(get_current_user)])
async def create_user(user_data: UserDTO, service: Annotated[UserService, Depends()]):
    new_user = await service.create_user(user_data)
    return new_user


# class DBSession:
#     def save(a, b):
#         debug_logger.debug(f"Hello from DBSession!")

# class Repository:
#     def __init__(self, db_session):
#         self.db_session = db_session

#     def save(self, a: int, b: int) -> None:
#         debug_logger.debug(f"Hello from repository!")
#         c = a + b
#         return c

# class Service:
#     def __init__(self, repository):
#         self.repository = repository

#     def do_stuff(self, a: int, b: int) -> int:
#         debug_logger.debug(f"Hello from service!")
#         self.repository.save(a, b)
#         return a + b

# def get_db_session():
#     return DBSession()

# def get_repository(db_session):
#     return Repository(db_session)

# def get_service(repository):
#     return Service(repository)

# @router.post('/')
# def controller(a: int, b: int):
#     db_session = get_db_session()
#     repository = get_repository(db_session)
#     service = get_service(repository)
#     debug_logger.debug(f"Hello from controller!")
#     res = service.do_stuff(a, b)
#     return {'result': res}
