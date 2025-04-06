from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(
    prefix='/api/users',
    tags=['Users']
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get('/chats')
def get_chats(user_id: int, token: Annotated[str, Depends(oauth2_scheme)]):
    ...

@router.post('/chats')
def create_chat(user_id: int, chat_data: dict):
    ...

@router.get('/{user_id}/chats')
def get_user_chats(user_id: int):
    ...

@router.delete('/{user_id}/chats/{chat_id}')
def delete_chat(user_id: int, chat_id: int):
    ...