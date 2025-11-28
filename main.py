# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
import random
import uvicorn

# -------------------------
# Config / Tips / Keywords
# -------------------------
DB_PATH = "wellness_bot.db"

MICROLEARNING_TIPS = [
    "💡 Take a 2-minute break every hour to refresh your mind.",
    "💡 Organize tasks in small chunks to reduce overwhelm.",
    "💡 Practice deep breathing for 1 minute to improve focus.",
    "💡 Write down your top 3 priorities for today.",
    "💡 Try positive self-talk when feeling stressed.",
    "💡 Stand up and stretch every hour to increase energy."
]

WELLNESS_REMINDERS = [
    "Remember to drink water regularly 💧",
    "Take short breaks to reduce fatigue 🧘‍♂️",
    "Maintain a healthy posture while working 🪑",
    "Avoid staring at screens for long periods 👀",
    "Practice gratitude daily 🌟",
    "Stay active: a quick walk helps your brain 🏃‍♂️"
]

STRESS_KEYWORDS = [
    "stress", "tired", "depressed", "sad", "angry",
    "anxious", "pressure", "overwhelmed", "burnout",
    "frustrated", "worried", "upset", "panic", "exhausted"
]

POSITIVE_WORDS = [
    "happy", "good", "great", "excited", "relaxed",
    "calm", "motivated", "fine", "awesome", "excellent"
]

# -------------------------
# DB helpers
# -------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        user_id TEXT,
        user_message TEXT,
        score INTEGER,
        stress_level TEXT,
        learning_tip TEXT,
        wellness_tip TEXT
    )
    """)
    conn.commit()
    conn.close()

def log_interaction(user_id, user_message, score, stress_level, learning_tip, wellness_tip):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT INTO interactions (timestamp, user_id, user_message, score, stress_level, learning_tip, wellness_tip)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (datetime.utcnow().isoformat(), user_id, user_message, score, stress_level, learning_tip, wellness_tip))
    conn.commit()
    conn.close()

# -------------------------
# Sentiment / logic
# -------------------------
def sentiment_score(text: str) -> int:
    t = text.lower()
    score = 0
    for w in POSITIVE_WORDS:
        if w in t:
            score += 1
    for w in STRESS_KEYWORDS:
        if w in t:
            score -= 2
    return score

def classify_stress(score: int) -> str:
    if score >= 1:
        return "Low"
    elif score == 0:
        return "Medium"
    else:
        return "High"

def burnout_risk_for_user(user_id: str, window_days: int = 7):
    """
    Simple rule: count High stress entries in the last `window_days`.
    Returns risk string.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    since = (datetime.utcnow() - timedelta(days=window_days)).isoformat()
    c.execute("""
    SELECT COUNT(*) FROM interactions
    WHERE user_id = ? AND timestamp >= ? AND stress_level = 'High'
    """, (user_id, since))
    count = c.fetchone()[0]
    conn.close()
    if count >= 6:
        return "High"
    elif count >= 4:
        return "Medium"
    else:
        return "Low"

# -------------------------
# FastAPI app
# -------------------------
app = FastAPI(title="Wellness Bot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

class AnalyzeRequest(BaseModel):
    text: str
    user_id: str = "anonymous"   # SalesIQ user id or any identifier

class AnalyzeResponse(BaseModel):
    reply: str
    score: int
    stress_level: str
    learning_tip: str
    wellness_tip: str
    burnout_risk: str = "Low"

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):

    text = request.text.lower()

    # ========== SIMPLE RULE-BASED CHECK ==========
    if "stress" in text or "tired" in text or "pressure" in text:
        reply_text = "I notice you might be feeling stressed. Try a 1-minute deep breathing exercise: Inhale 4s • Hold 4s • Exhale 4s."
        stress_level = "High"
        confidence = 0.95
        response_type = "emotion"

    else:
        reply_text = "You're doing good! Let me know if you'd like help with something."
        stress_level = "Low"
        confidence = 0.85
        response_type = "neutral"

    # ========== IMPORTANT: ZOHO-FRIENDLY RETURN ==========
    return {
    "reply_text": reply_text,
    "stress_level": stress_level,
    "score": confidence,
    "type": response_type
}



# -------------------------
# Analytics endpoints
# -------------------------
@app.get("/analytics/summary")
def analytics_summary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # total interactions
    c.execute("SELECT COUNT(*) FROM interactions")
    total = c.fetchone()[0]

    # distribution of stress levels
    c.execute("SELECT stress_level, COUNT(*) FROM interactions GROUP BY stress_level")
    dist = {row[0]: row[1] for row in c.fetchall()}

    # last 30 days daily average score
    c.execute("""
    SELECT substr(timestamp,1,10) as day, AVG(score)
    FROM interactions
    WHERE timestamp >= ?
    GROUP BY day
    ORDER BY day
    """, ((datetime.utcnow() - timedelta(days=30)).isoformat(),))
    daily = [{"day": r[0], "avg_score": r[1]} for r in c.fetchall()]

    conn.close()
    return {"total_interactions": total, "distribution": dist, "daily_avg_score": daily}

@app.get("/analytics/recent")
def analytics_recent(limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    SELECT timestamp, user_id, user_message, score, stress_level, learning_tip, wellness_tip
    FROM interactions
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    results = []
    for r in rows:
        results.append({
            "timestamp": r[0],
            "user_id": r[1],
            "user_message": r[2],
            "score": r[3],
            "stress_level": r[4],
            "learning_tip": r[5],
            "wellness_tip": r[6]
        })
    return {"recent": results}

# health
@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

# -------------------------
# Run server (for local testing)
# -------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
