import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="CEO-PULSE SOVEREIGN API", version="10.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AdvisorRequest(BaseModel):
    question: str
    liquidity: Optional[float] = 1066875.0
    net_profit: Optional[float] = 271500.0
    burn_rate: Optional[float] = 29800.0
    currency: Optional[str] = "SAR"

class CVRequest(BaseModel):
    job_title: str
    cv_text: str

def ask_sovereign_brain(prompt: str) -> str:
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not groq_key:
        raise Exception("يرجى إضافة مفتاح GROQ_API_KEY في إعدادات Render")

    url = "https://groq.com"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "أنت المستشار الاستراتيجي التنفيذي لمنظومة CEO-PULSE. أجب باللغة العربية باختصار حاسم في 3 نقاط تنفيذية مرقمة."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 500
    }
    res = requests.post(url, headers=headers, json=body, timeout=20)
    if res.status_code == 200:
        data = res.json()
        first_choice = next(iter(data.get("choices", list())), {})
        return first_choice.get("message", {}).get("content", "")
    raise Exception(f"HTTP {res.status_code}: {res.text[:120]}")

@app.get("/")
def home():
    return {
        "status": "ONLINE",
        "system": "CEO-PULSE SOVEREIGN v10.0-Groq",
        "ai_engine": "Connected" if os.environ.get("GROQ_API_KEY") else "Missing GROQ_API_KEY"
    }

@app.post("/api/ai-advisor")
async def run_ai_advisor(payload: AdvisorRequest):
    q = payload.question.strip()
    if not q:
        return {"status": "error", "reply": "⚠️ الرجاء كتابة سؤالك أولاً."}

    runway = round(payload.liquidity / payload.burn_rate, 1) if payload.burn_rate > 0 else 12.0

    try:
        prompt = f"بيانات الشركة الحية: السيولة {payload.liquidity:,.0f} {payload.currency}، الأرباح {payload.net_profit:,.0f} {payload.currency}، الحرق الشهري {payload.burn_rate:,.0f} {payload.currency}، مدرج الأمان {runway} شهر. سؤال المدير: '{q}'."
        reply_text = ask_sovereign_brain(prompt)
        return {"status": "success", "reply": reply_text}
    except Exception as e:
        return {"status": "error", "reply": f"⚠️ تنبيه: {str(e)}"}

@app.post("/api/parse-cv")
async def parse_cv(payload: CVRequest):
    try:
        prompt = f"قيّم هذه السيرة الذاتية لوظيفة '{payload.job_title}': {payload.cv_text}. أرجع JSON فقط بدون أي نص إضافي بالمفاتيح: candidate_name, match_score, summary, whatsapp_invite."
        raw = ask_sovereign_brain(prompt)
        clean_json = raw.replace("```json", "").replace("```", "").strip()
        return {"status": "success", "analysis": json.loads(clean_json)}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
