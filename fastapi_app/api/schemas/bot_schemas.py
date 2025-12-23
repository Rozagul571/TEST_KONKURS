# fastapi_app/api/schemas/bot_schemas.py:
from pydantic import BaseModel

class UserCompletedPayload(BaseModel):
    user_tg_id: int
    competition_name: str
    description: str

class RunBotRequest(BaseModel):
    token: str
    username: str
    user_id: int

class StopBotRequest(BaseModel):
    user_id: int
    username: str

class BotResponse(BaseModel):
    id: int
    username: str
    status: str
    owner_id: int