import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from google import genai
from google.genai import types

app = FastAPI(
    title="CEO-PULSE SOVEREIGN API",
    version="8.5.0",
    description="Universal Executive OS & Auto-Detect AI Engine"
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

# دالة ذكية تجلب اسم النموذج المتاح تلقائياً في حسابك
def get_available_model(client):
    try:
        for m in client.models.list():
            if "generateContent" in (m.supported_actions or []):
                if "flash" in m.name.lower():
                    return m.name
        for m in client.models.list():
            if "generateContent" in (m.supported_actions or []):
                return m.name
    except Exception:
        pass
    return "gemini-2.0-flash"

@app.get("/")
def home():
    api_status = "Connected" if os.environ.get("GEMINI_API_KEY") else "Missing Key"
    return {
        "status": "ONLINE",
        "system": "CEO-PULSE SOVEREIGN v8.5-live",
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
        client = genai.Client(api_key=api_key)
        active_model = get_available_model(client)
        
        prompt = f"""
        أنت المستشار الاستراتيجي التنفيذي لمنظومة CEO-PULSE.
        بيانات الشركة: السيولة {payload.liquidity:,.0f} {payload.currency}، الأرباح {payload.net_profit:,.0f} {payload.currency}، الحرق الشهري {payload.burn_rate:,.0f} {payload.currency}، مدرج الأمان {runway_months} شهر.
        سؤال المدير: "{q}"
        أجب باختصار شديد في 3 نقاط تنفيذية حاسمة.
        """
        response = client.models.generate_content(
            model=active_model,
            contents=prompt,
        )
        return {
            "status": "success",
            "reply": response.text
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
        client = genai.Client(api_key=api_key)
        active_model = get_available_model(client)
        
        prompt = f"""
        قيّم هذه السيرة الذاتية لوظيفة: "{payload.job_title}".
        النص: {payload.cv_text}
        أرجع النتيجة بصيغة JSON بالمفاتيح: "candidate_name", "match_score", "summary", "whatsapp_invite".
        """
        response = client.models.generate_content(
            model=active_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return {
            "status": "success",
            "analysis": json.loads(response.text)
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
