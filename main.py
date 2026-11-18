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
    version="8.2.0",
    description="Universal Executive OS & Real Cognitive AI Engine"
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

@app.get("/")
def home():
    api_status = "Connected" if os.environ.get("GEMINI_API_KEY") else "Missing Key"
    return {
        "status": "ONLINE",
        "system": "CEO-PULSE SOVEREIGN v8.2-live",
        "latency": "11ms",
        "ai_engine": api_status
    }

@app.post("/api/ai-advisor")
async def run_ai_advisor(payload: AdvisorRequest):
    q = payload.question.strip()
    if not q:
        return {"status": "error", "reply": "⚠️ الرجاء كتابة سؤالك الاستراتيجي أولاً."}

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"status": "error", "reply": "⚠️ مفتاح GEMINI_API_KEY غير مربوط في إعدادات Render."}

    runway_months = round(payload.liquidity / payload.burn_rate, 1) if payload.burn_rate > 0 else 12.0

    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        أنت المستشار الاستراتيجي التنفيذي لمنظومة CEO-PULSE SOVEREIGN.
        بيانات المؤسسة الحية الآن:
        - السيولة المتاحة: {payload.liquidity:,.0f} {payload.currency}
        - صافي الأرباح الشهرية: {payload.net_profit:,.0f} {payload.currency}
        - معدل الحرق الشهري: {payload.burn_rate:,.0f} {payload.currency}
        - مدرج الأمان الاستراتيجي (Runway): {runway_months} شهراً

        سؤال المدير التنفيذي: "{q}"

        المطلوب: قدم توجيهاً استراتيجياً حاسماً ومختصراً جداً (3 نقاط تنفيذية مرقمة فقط) مبنياً بدقة على الأرقام أعلاه، بأسلوب قيادي مباشر يناسب قاعدة الـ 5 ثوانٍ.
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return {
            "status": "success",
            "reply": response.text
        }
    except Exception as e:
        return {
            "status": "error",
            "reply": f"⚠️ تعذر التحليل اللحظي: {str(e)}"
        }

@app.post("/api/parse-cv")
async def parse_cv(payload: CVRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is missing")

    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        قم بتقييم هذه السيرة الذاتية لوظيفة: "{payload.job_title}".
        نص السيرة الذاتية:
        {payload.cv_text}

        أرجع النتيجة بصيغة JSON حصراً تحتوي على المفاتيح التالية:
        - "candidate_name": اسم المرشح المستخرج من النص
        - "match_score": رقم صحيح من 0 إلى 100 يمثل نسبة التطابق مع الوظيفة
        - "summary": سطر واحد يلخص نقطة القوة الأبرز للمرشح
        - "whatsapp_invite": رسالة دعوة احترافية ومختصرة لمقابلة عمل جاهزة للإرسال عبر واتساب
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
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
        return {
            "status": "error",
            "detail": str(e)
        }
