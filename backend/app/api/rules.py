"""
정책(임계값) 설정 API. ('정책 설정' 기능)

- GET   /rules : 현재 판정 임계값 (경고/승인/차단 경계)
- PATCH /rules : 임계값 수정 (0~100, warn < approve < block)
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session
from app.database import get_session
from app.models import PolicyThreshold

router = APIRouter()


@router.get("/rules")
def get_rules(db: Session = Depends(get_session)):
    th = db.get(PolicyThreshold, 1)
    return {"warn": th.warn, "approve": th.approve, "block": th.block}


class RuleUpdate(BaseModel):
    warn: Optional[int] = None
    approve: Optional[int] = None
    block: Optional[int] = None


@router.patch("/rules")
def update_rules(body: RuleUpdate, db: Session = Depends(get_session)):
    th = db.get(PolicyThreshold, 1)
    warn = body.warn if body.warn is not None else th.warn
    approve = body.approve if body.approve is not None else th.approve
    block = body.block if body.block is not None else th.block

    for v in (warn, approve, block):
        if not (0 <= v <= 100):
            raise HTTPException(400, "임계값은 0~100 사이여야 합니다")
    if not (warn < approve < block):
        raise HTTPException(400, "경고 < 승인 < 차단 순서를 지켜야 합니다")

    th.warn, th.approve, th.block = warn, approve, block
    db.add(th); db.commit(); db.refresh(th)
    return {"warn": th.warn, "approve": th.approve, "block": th.block}