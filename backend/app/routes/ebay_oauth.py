from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.market.ebay_client import (
    EbayAuthError,
    get_oauth_authorize_url,
    exchange_code_for_refresh_token,
)

router = APIRouter()


class ExchangeRequest(BaseModel):
    code: str


@router.get("/authorize")
async def authorize():
    url = get_oauth_authorize_url()
    return {"authorize_url": url}


@router.post("/exchange")
async def exchange(payload: ExchangeRequest):
    try:
        token = exchange_code_for_refresh_token(payload.code)
    except EbayAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"refresh_token": token, "connected": True}
