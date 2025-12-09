from pydantic import BaseModel

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