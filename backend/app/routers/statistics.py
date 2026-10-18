"""统计接口：月度汇总与分类占比。金额计算全部在后端 SQL 完成。"""
import calendar
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Bill, BillCategory, User
from app.schemas import CategoryStatItem, CategoryStatsOut, DayPoint, MonthlyStatsOut

router = APIRouter()


def _parse_month(month: str) -> tuple[int, int]:
    try:
        year, mon = int(month[:4]), int(month[5:7])
        assert 1 <= mon <= 12
        return year, mon
    except (ValueError, AssertionError):
        raise HTTPException(400, "月份格式应为 YYYY-MM")


def _month_days(year: int, mon: int) -> list[date]:
    return [date(year, mon, d) for d in range(1, calendar.monthrange(year, mon)[1] + 1)]


@router.get("/monthly", response_model=MonthlyStatsOut)
def monthly(month: str = "", user: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    today = date.today()
    month = month or today.strftime("%Y-%m")
    year, mon = _parse_month(month)

    rows = db.scalars(select(Bill).where(
        Bill.user_id == user.id,
        extract("year", Bill.bill_date) == year,
        extract("month", Bill.bill_date) == mon,
    )).all()

    income = sum((r.amount for r in rows if r.type == "income"), Decimal("0"))
    expense = sum((r.amount for r in rows if r.type == "expense"), Decimal("0"))
    by_day: dict[date, dict] = {
        d: {"expense": Decimal("0"), "income": Decimal("0")} for d in _month_days(year, mon)}
    for r in rows:
        by_day[r.bill_date][r.type] += r.amount

    return MonthlyStatsOut(
        month=month, income=income, expense=expense, net=income - expense,
        count=len(rows),
        days=[DayPoint(date=d, expense=v["expense"], income=v["income"])
              for d, v in by_day.items()])


@router.get("/categories", response_model=CategoryStatsOut)
def categories(month: str = "", type: str = "expense",
               user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    month = month or today.strftime("%Y-%m")
    if type not in ("income", "expense"):
        raise HTTPException(400, "type 只能为 income 或 expense")
    year, mon = _parse_month(month)

    rows = db.execute(
        select(BillCategory.name, func.sum(Bill.amount))
        .join(Bill, Bill.category_id == BillCategory.id)
        .where(
            Bill.user_id == user.id,
            Bill.type == type,
            extract("year", Bill.bill_date) == year,
            extract("month", Bill.bill_date) == mon,
        )
        .group_by(BillCategory.name)
        .order_by(func.sum(Bill.amount).desc())
    ).all()

    total = sum((amount for _, amount in rows), Decimal("0"))
    items = [
        CategoryStatItem(
            category=name,
            amount=Decimal(str(amount)),
            ratio=round(float(Decimal(str(amount)) / total), 4) if total > 0 else 0.0)
        for name, amount in rows
    ]
    return CategoryStatsOut(month=month, type=type, total=total, items=items)
