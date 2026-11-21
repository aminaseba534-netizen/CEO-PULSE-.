import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from groq import Groq

app = FastAPI(title="CEO-PULSE SOVEREIGN API", version="10.2.0")

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

def ask_groq_official(prompt: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise Exception("مفتاح GROQ_API_KEY غير موجود في إعدادات Render")

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=list((
            {
                "role": "system",
                "content": "أنت المستشار الاستراتيجي التنفيذي لمنظومة CEO-PULSE. أجب باللغة العربية باختصار حاسم في 3 نقاط تنفيذية مرقمة فقط."
            },
            {
                "role": "user",
                "content": prompt
            }
        )),
        temperature=0.4,
        max_tokens=500
    )
    first_choice = next(iter(completion.choices))
    return first_choice.message.content

@app.get("/")
def home():
    return {
        "status": "ONLINE",
        "system": "CEO-PULSE SOVEREIGN v10.2-OfficialGroq",
        "ai_engine": "Connected" if os.environ.get("GROQ_API_KEY") else "Missing Key"
    }

@app.post("/api/ai-advisor")
async def run_ai_advisor(payload: AdvisorRequest):
    q = payload.question.strip()
    if not q:
        return {"status": "error", "reply": "⚠️ الرجاء كتابة سؤالك أولاً."}

    runway = round(payload.liquidity / payload.burn_rate, 1) if payload.burn_rate > 0 else 12.0

    try:
        prompt = f"بيانات الشركة الحية: السيولة {payload.liquidity:,.0f} {payload.currency}، الأرباح {payload.net_profit:,.0f} {payload.currency}، الحرق الشهري {payload.burn_rate:,.0f} {payload.currency}، مدرج الأمان {runway} شهر. سؤال المدير: '{q}'."
        reply_text = ask_groq_official(prompt)
        return {"status": "success", "reply": reply_text}
    except Exception as e:
        return {"status": "error", "reply": f"⚠️ تنبيه: {str(e)}"}

@app.post("/api/parse-cv")
async def parse_cv(payload: CVRequest):
    try:
        prompt = f"قيّم هذه السيرة الذاتية لوظيفة '{payload.job_title}': {payload.cv_text}. أرجع JSON فقط بدون أي نص إضافي بالمفاتيح: candidate_name, match_score, summary, whatsapp_invite."
        raw = ask_groq_official(prompt)
        clean_json = raw.replace("```json", "").replace("```", "").strip()
        return {"status": "success", "analysis": json.loads(clean_json)}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
