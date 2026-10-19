"""生活挑战接口：按周期统计分类支出、与上一周期对比（后端计算）。"""
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Bill, BillCategory, Challenge, User
from app.schemas import ChallengeIn, ChallengeOut

router = APIRouter()


def _resolve_category(db: Session, user: User, name: str) -> BillCategory:
    cat = db.scalar(select(BillCategory).where(
        BillCategory.name == name,
        (BillCategory.user_id.is_(None)) | (BillCategory.user_id == user.id)).limit(1))
    if cat is None:
        raise HTTPException(400, f"分类“{name}”不存在")
    return cat


def _spend(db: Session, user_id: int, category_id: int,
           start: date, end: date) -> Decimal:
    rows = db.scalars(select(Bill).where(
        Bill.user_id == user_id, Bill.category_id == category_id,
        Bill.bill_date >= start, Bill.bill_date <= end)).all()
    return sum((Decimal(str(b.amount)) for b in rows), Decimal("0"))


def _to_out(db: Session, user: User, row: Challenge) -> ChallengeOut:
    today = date.today()
    current = _spend(db, user.id, row.category_id, row.start_date, row.end_date)
    prev_start = row.start_date - timedelta(days=row.period_days)
    prev_end = row.start_date - timedelta(days=1)
    previous = _spend(db, user.id, row.category_id, prev_start, prev_end)
    change_pct = round(float((current - previous) / previous * 100), 1) \
        if previous > 0 else None
    target = Decimal(str(row.target_amount))
    ratio = float(current / target) if target > 0 else 0.0
    if today > row.end_date:
        status = "finished" if current <= target else "failed"
    else:
        status = "on_track" if current <= target else "over"
    cat = db.get(BillCategory, row.category_id) if row.category_id else None
    return ChallengeOut(
        id=row.id, name=row.name, category=cat.name if cat else "全部",
        period_days=row.period_days, target_amount=target,
        start_date=row.start_date, end_date=row.end_date,
        current_spend=current.quantize(Decimal("0.01")),
        previous_spend=previous.quantize(Decimal("0.01")) if previous > 0 else None,
        change_pct=change_pct, progress_ratio=round(ratio, 4),
        status=status, days_left=max(0, (row.end_date - today).days))


@router.get("", response_model=list[ChallengeOut])
def list_challenges(user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    rows = db.scalars(select(Challenge).where(Challenge.user_id == user.id)
                      .order_by(Challenge.created_at.desc())).all()
    return [_to_out(db, user, r) for r in rows]


@router.post("", response_model=ChallengeOut)
def create_challenge(data: ChallengeIn, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    cat = _resolve_category(db, user, data.category)
    start = date.today()
    row = Challenge(
        user_id=user.id, name=data.name, category_id=cat.id,
        period_days=data.period_days, target_amount=data.target_amount,
        start_date=start, end_date=start + timedelta(days=data.period_days - 1))
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_out(db, user, row)


@router.delete("/{challenge_id}")
def delete_challenge(challenge_id: int, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    row = db.get(Challenge, challenge_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(404, "挑战不存在")
    db.delete(row)
    db.commit()
    return {"ok": True}
