from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    text: str
    user_id: str

class AnalyzeResponse(BaseModel):
    replies: list
    stress_level: str
    score: float
    type: str

