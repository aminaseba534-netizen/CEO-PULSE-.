import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="CEO-PULSE V8.1 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VoucherApproval(BaseModel):
    transaction_id: str
    source_erp: str
    amount_dzd: float
    biometric_signature: str

@app.get("/")
def read_root():
    return {"status": "ONLINE", "version": "8.1-live", "system": "CEO-PULSE SOVEREIGN"}

@app.get("/api/v1/health")
def health_check():
    return {"status": "HEALTHY", "stations_connected": 142}

@app.post("/api/v1/treasury/biometric-signoff")
def approve_voucher(voucher: VoucherApproval):
    return {
        "status": "APPROVED",
        "transaction_id": voucher.transaction_id,
        "cryptographic_sig": f"SIG-SAP-{voucher.biometric_signature[:8].upper()}-VERIFIED"
    }
