from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ----------------------
# REQUEST MODEL
# ----------------------
class AnalyzeRequest(BaseModel):
    text: str
    user_id: str = "anonymous"

# ----------------------
# API ENDPOINT
# ----------------------
@app.post("/analyze")
async def analyze(req: AnalyzeRequest):

    text = req.text.lower()

    # Simple logic
    if "stress" in text or "sad" in text or "tired" in text:
        reply = "I notice you're feeling stressed. Try a deep breath: inhale 4s, hold 4s, exhale 4s."
        stress_level = "High"
        score = 0.95
        msg_type = "emotion"
    else:
        reply = "You're doing good! Let me know if you need help."
        stress_level = "Low"
        score = 0.85
        msg_type = "neutral"

    # -------------------------
    # ZOHO REQUIRED FORMAT
    # -------------------------
    return {
        "replies": [
            {"text": reply}
        ],
        "stress_level": stress_level,
        "score": score,
        "type": msg_type
    }


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
