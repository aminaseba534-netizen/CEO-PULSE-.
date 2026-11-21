import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="CEO-PULSE SOVEREIGN API",
    version="9.0.0",
    description="Auto-Discovery Sovereign AI Engine"
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

def call_gemini_smart(api_key: str, prompt: str) -> str:
    clean_key = api_key.strip()
    base_host = "https://googleapis.com"
    
    # 1. جلب قائمة النماذج المفعلة فعلياً في حسابك
    models_to_try = list(("models/gemini-3.8-flash", "models/gemini-2.5-flash"))
    try:
        list_res = requests.get(f"{base_host}/models?key={clean_key}", timeout=10)
        if list_res.status_code == 200:
            available = list_res.json().get("models", list())
            flash_models = list(
                m.get("name") for m in available 
                if "generateContent" in m.get("supportedGenerationMethods", list()) 
                and "flash" in m.get("name", "").lower()
            )
            if flash_models:
                models_to_try = flash_models
    except Exception:
        pass

    last_error = ""
    for full_model_name in models_to_try:
        # التأكد من صيغة الاسم (models/...)
        model_path = full_model_name if full_model_name.startswith("models/") else f"models/{full_model_name}"
        url = f"{base_host}/{model_path}:generateContent?key={clean_key}"
        
        body = {
            "contents": list((
                {"parts": list(({"text": prompt},))},
            ))
        }
        try:
            response = requests.post(url, headers={"Content-Type": "application/json"}, json=body, timeout=25)
            if response.status_code == 200:
                data = response.json()
                first_cand = next(iter(data.get("candidates", list())), {})
                parts = first_cand.get("content", {}).get("parts", list())
                first_part = next(iter(parts), {})
                text = first_part.get("text", "")
                if text:
                    return text
            last_error = f"{model_path} -> HTTP {response.status_code}: {response.text[:120]}"
        except Exception as e:
            last_error = str(e)
            continue

    raise Exception(f"تفاصيل الخطأ: {last_error}")

@app.get("/")
def home():
    api_status = "Connected" if os.environ.get("GEMINI_API_KEY") else "Missing Key"
    return {
        "status": "ONLINE",
        "system": "CEO-PULSE SOVEREIGN v9.0-live",
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
        reply_text = call_gemini_smart(api_key, prompt)
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
        raw_text = call_gemini_smart(api_key, prompt)
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        return {
            "status": "success",
            "analysis": json.loads(clean_json)
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
