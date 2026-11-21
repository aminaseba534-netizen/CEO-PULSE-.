import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="CEO-PULSE SOVEREIGN API",
    version="8.8.0",
    description="Direct Sovereign AI Engine"
)

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

def call_gemini_direct(api_key: str, prompt: str) -> str:
    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    last_error = ""
    base_host = "https://googleapis.com"

    for model_name in models:
        url = base_host + "/v1beta/models/" + model_name + ":generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": api_key.strip()}
        body = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        try:
            response = requests.post(url, headers=headers, params=params, json=body, timeout=25)
            if response.status_code == 200:
                result = response.json()
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            last_error = f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            last_error = str(e)
            continue

    raise Exception(f"تفاصيل الخطأ: {last_error}")

@app.get("/")
def home():
    api_status = "Connected" if os.environ.get("GEMINI_API_KEY") else "Missing Key"
    return {
        "status": "ONLINE",
        "system": "CEO-PULSE SOVEREIGN v8.8-live",
        "ai_engine": api_status
    }

@app.post("/api/ai-advisor")
async def run_ai_advisor(payload: AdvisorRequest):
    q = payload.question.strip()
    if not q:
        return {"status": "error", "reply": "⚠️ الرجاء كتابة سؤالك الاستراتيجي أولاً."}

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"status": "error", "reply": "⚠️ مفتاح GEMINI_API_KEY غير مربوط."}

    runway_months = round(payload.liquidity / payload.burn_rate, 1) if payload.burn_rate > 0 else 12.0

    try:
        prompt = f"""
        أنت المستشار الاستراتيجي التنفيذي لمنظومة CEO-PULSE.
        بيانات الشركة: السيولة {payload.liquidity:,.0f} {payload.currency}، الأرباح {payload.net_profit:,.0f} {payload.currency}، الحرق الشهري {payload.burn_rate:,.0f} {payload.currency}، مدرج الأمان {runway_months} شهر.
        سؤال المدير: "{q}"
        أجب باختصار شديد في 3 نقاط تنفيذية حاسمة.
        """
        reply_text = call_gemini_direct(api_key, prompt)
        return {
            "status": "success",
            "reply": reply_text
        }
    except Exception as e:
        return {
            "status": "error",
            "reply": f"⚠️ تنبيه السيرفر: {str(e)}"
        }

@app.post("/api/parse-cv")
async def parse_cv(payload: CVRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is missing")

    try:
        prompt = f"""
        قيّم هذه السيرة الذاتية لوظيفة: "{payload.job_title}".
        النص: {payload.cv_text}
        أرجع النتيجة بصيغة JSON فقط بدون أي نص إضافي بالمفاتيح: "candidate_name", "match_score", "summary", "whatsapp_invite".
        """
        raw_text = call_gemini_direct(api_key, prompt)
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        return {
            "status": "success",
            "analysis": json.loads(clean_json)
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
