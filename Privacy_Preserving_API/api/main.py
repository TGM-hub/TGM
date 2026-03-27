"""
api/main.py -- FastAPI server for privacy-preserving analytics.

Receives ciphertexts, computes statistics, returns encrypted results.
The server never imports encryption.py -- it has no business decrypting anything.
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List
from crypto.operations import encrypted_sum, encrypted_mean


# Schemas
class EncryptedDataRequest(BaseModel):
    ciphertexts: List[float] = Field(..., min_length=1)


class StatResult(BaseModel):
    encrypted_result: float
    count: int


# App
app = FastAPI(
    title="Privacy-Preserving Analytics API",
    description="Compute statistics on encrypted data. The server never sees raw values.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/analytics/sum", response_model=StatResult)
def compute_sum(payload: EncryptedDataRequest) -> StatResult:
    result = encrypted_sum(payload.ciphertexts)
    return StatResult(encrypted_result=result, count=len(payload.ciphertexts))


@app.post("/analytics/mean", response_model=StatResult)
def compute_mean(payload: EncryptedDataRequest) -> StatResult:
    result, n = encrypted_mean(payload.ciphertexts)
    return StatResult(encrypted_result=result, count=n)