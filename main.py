import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="CEO-PULSE SOVEREIGN API", version="9.3.0")

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

def ask_google_ai(api_key: str, prompt: str) -> str:
    clean_key = api_key.strip()
    body = {
        "contents": list((
            {"role": "user", "parts": list(({"text": prompt},))},
        ))
    }
    
    # النماذج الحديثة المعتمدة في 2026 للمفاتيح الجديدة
    models = list(("gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.0-flash", "gemini-2.5-flash"))
    bases = list((
        "https://googleapis.com",
        "https://googleapis.com"
    ))
    
    last_err = ""
    for base in bases:
        for model in models:
            url = f"{base}/{model}:generateContent"
            try:
                res = requests.post(url, params={"key": clean_key}, json=body, timeout=25)
                if res.status_code == 200:
                    data = res.json()
                    first_cand = next(iter(data.get("candidates", list())), {})
                    parts = first_cand.get("content", {}).get("parts", list())
                    first_part = next(iter(parts), {})
                    text = first_part.get("text", "")
                    if text:
                        return text
                last_err = f"{model} -> HTTP {res.status_code}: {res.text[:100]}"
            except Exception as e:
                last_err = str(e)
            
    raise Exception(last_err)

@app.get("/")
def home():
    return {
        "status": "ONLINE",
        "system": "CEO-PULSE SOVEREIGN v9.3-live",
        "ai_engine": "Connected" if os.environ.get("GEMINI_API_KEY") else "Missing Key"
    }

@app.post("/api/ai-advisor")
async def run_ai_advisor(payload: AdvisorRequest):
    q = payload.question.strip()
    if not q:
        return {"status": "error", "reply": "⚠️ الرجاء كتابة سؤالك أولاً."}

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"status": "error", "reply": "⚠️ مفتاح API غير موجود في Render."}

    runway = round(payload.liquidity / payload.burn_rate, 1) if payload.burn_rate > 0 else 12.0

    try:
        prompt = f"أنت المستشار التنفيذي لمنظومة CEO-PULSE. السيولة: {payload.liquidity:,.0f} {payload.currency}، الأرباح: {payload.net_profit:,.0f} {payload.currency}، الحرق الشهري: {payload.burn_rate:,.0f} {payload.currency}، مدرج الأمان: {runway} شهر. سؤال المدير: '{q}'. أجب باختصار في 3 نقاط تنفيذية حاسمة."
        reply_text = ask_google_ai(api_key, prompt)
        return {"status": "success", "reply": reply_text}
    except Exception as e:
        return {"status": "error", "reply": f"⚠️ تنبيه: {str(e)}"}

@app.post("/api/parse-cv")
async def parse_cv(payload: CVRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing API Key")

    try:
        prompt = f"قيّم هذه السيرة الذاتية لوظيفة '{payload.job_title}': {payload.cv_text}. أرجع JSON فقط بالمفاتيح: candidate_name, match_score, summary, whatsapp_invite."
        raw = ask_google_ai(api_key, prompt)
        clean_json = raw.replace("```json", "").replace("```", "").strip()
        return {"status": "success", "analysis": json.loads(clean_json)}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
