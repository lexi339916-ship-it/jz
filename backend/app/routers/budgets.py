"""预算接口：按月设置预算并计算使用情况。"""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Bill, Budget, User
from app.schemas import BudgetIn, BudgetOut

router = APIRouter()


def _month_condition(user_id: int, month: str):
    year, mon = int(month[:4]), int(month[5:7])
    return [
        Bill.user_id == user_id,
        Bill.type == "expense",
        extract("year", Bill.bill_date) == year,
        extract("month", Bill.bill_date) == mon,
    ]


@router.get("", response_model=BudgetOut)
def get_budget(month: str, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    row = db.scalar(select(Budget).where(
        Budget.user_id == user.id, Budget.month == month))
    spent = db.scalar(select(func.coalesce(func.sum(Bill.amount), 0))
                      .where(*_month_condition(user.id, month)))
    amount = row.amount if row else Decimal("0")
    spent = Decimal(str(spent))
    ratio = float(spent / amount) if amount > 0 else 0.0
    return BudgetOut(month=month, amount=amount, spent=spent,
                     remaining=amount - spent, usage_ratio=round(ratio, 4))


@router.put("", response_model=BudgetOut)
def set_budget(data: BudgetIn, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    if data.amount <= 0:
        raise HTTPException(400, "预算金额必须大于 0")
    row = db.scalar(select(Budget).where(
        Budget.user_id == user.id, Budget.month == data.month))
    if row is None:
        row = Budget(user_id=user.id, month=data.month, amount=data.amount)
        db.add(row)
    else:
        row.amount = data.amount
    db.commit()
    return get_budget(data.month, user=user, db=db)
