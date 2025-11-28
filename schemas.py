from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    text: str
    user_id: str

class AnalyzeResponse(BaseModel):
    reply: str
    stress_level: str
    score: float
    type: str  # "learning" or "emotion"
