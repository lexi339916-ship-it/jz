"""分类接口：系统预置 + 用户自定义分类。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Bill, BillCategory, User
from app.schemas import CategoryIn, CategoryOut

router = APIRouter()


def _to_out(row: BillCategory) -> CategoryOut:
    return CategoryOut(id=row.id, name=row.name, type=row.type, is_system=row.user_id is None)


@router.get("")
def list_categories(type: str = "", user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    query = select(BillCategory).where(
        (BillCategory.user_id.is_(None)) | (BillCategory.user_id == user.id))
    if type in ("income", "expense"):
        query = query.where(BillCategory.type == type)
    rows = db.scalars(query.order_by(BillCategory.user_id.is_(None).desc(),
                                     BillCategory.id)).all()
    return {"items": [_to_out(r).model_dump() for r in rows]}


@router.post("", response_model=CategoryOut)
def create_category(data: CategoryIn, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    dup = db.scalar(select(BillCategory).where(
        BillCategory.user_id == user.id,
        BillCategory.name == data.name,
        BillCategory.type == data.type))
    if dup:
        raise HTTPException(400, "该分类已存在")
    row = BillCategory(user_id=user.id, name=data.name, type=data.type)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_out(row)


@router.delete("/{category_id}")
def delete_category(category_id: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    row = db.get(BillCategory, category_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(404, "分类不存在或无权删除")
    used = db.scalar(select(Bill.id).where(Bill.category_id == category_id).limit(1))
    if used is not None:
        raise HTTPException(400, "该分类下仍有账单，无法删除")
    db.delete(row)
    db.commit()
    return {"ok": True}
