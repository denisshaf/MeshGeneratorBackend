from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from ..utils.authentication import get_current_user

router = APIRouter(
    prefix='/api',
    tags=['Users']
)


# Protected endpoint example
@router.get("/protected")
async def protected_route(user=Depends(get_current_user)):
    return {"message": "This is a protected endpoint", "user": user}

# Public endpoint example
@router.get("/public")
async def public_route():
    return {"message": "This is a public endpoint"}

# @router.get('/chats')
# def get_chats(user_id: int):
#     ...

# @router.post('/chats')
# def create_chat(user_id: int, chat_data: dict):
#     ...

# @router.get('/{user_id}/chats')
# def get_user_chats(user_id: int):
#     ...

# @router.delete('/{user_id}/chats/{chat_id}')
# def delete_chat(user_id: int, chat_id: int):
#     ...