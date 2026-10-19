"""便签与任务接口：CRUD、搜索、视图过滤（今天/近期/已完成）、优先级与置顶。"""
from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Note, User
from app.schemas import NoteIn, NoteOut, NotePageOut

router = APIRouter()


def _to_out(row: Note) -> NoteOut:
    overdue = (
        row.note_type == "todo" and row.status == "open"
        and row.due_at is not None and row.due_at < datetime.now())
    return NoteOut(
        id=row.id, title=row.title, content=row.content,
        note_type=row.note_type, status=row.status, due_at=row.due_at,
        priority=row.priority, pinned=bool(row.pinned), is_overdue=overdue,
        created_at=row.created_at, updated_at=row.updated_at)


def _get_owned(db: Session, user: User, note_id: int) -> Note:
    row = db.get(Note, note_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(404, "便签不存在")
    return row


@router.get("", response_model=NotePageOut)
def list_notes(
    q: str = "",
    note_type: str = "",
    status: str = "",
    view: str = "",          # ""全部 / today今天 / upcoming近期 / done已完成
    page: int = 1,
    page_size: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conditions = [Note.user_id == user.id]
    if q:
        conditions.append((Note.title + Note.content).like(f"%{q}%"))
    if note_type in ("note", "todo"):
        conditions.append(Note.note_type == note_type)
    if status in ("open", "done"):
        conditions.append(Note.status == status)

    now = datetime.now()
    today_start = datetime.combine(now.date(), time.min)
    tomorrow_start = today_start + timedelta(days=1)

    if view == "today":
        # 今天到期 + 已逾期（仍未完成）
        conditions += [Note.note_type == "todo", Note.status == "open",
                       Note.due_at.isnot(None), Note.due_at < tomorrow_start]
    elif view == "upcoming":
        # 明天及以后到期的未完成任务
        conditions += [Note.note_type == "todo", Note.status == "open",
                       Note.due_at.isnot(None), Note.due_at >= tomorrow_start]
    elif view == "done":
        conditions += [Note.note_type == "todo", Note.status == "done"]

    total = db.scalar(select(func.count()).where(*conditions)) or 0
    pending = db.scalar(select(func.count()).where(
        Note.user_id == user.id, Note.note_type == "todo", Note.status == "open")) or 0

    # 排序：置顶 → 未完成在前 → 有截止时间的在前（按时间）→ 优先级 → 最近更新
    priority_order = case(
        (Note.priority == "high", 0), (Note.priority == "medium", 1), else_=2)
    rows = db.scalars(
        select(Note).where(*conditions)
        .order_by(
            Note.pinned.desc(),
            case((Note.status == "open", 0), else_=1),
            Note.due_at.is_(None),
            Note.due_at.asc(),
            priority_order.asc(),
            Note.updated_at.desc(),
        )
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    return NotePageOut(items=[_to_out(r) for r in rows], total=total, pending_count=pending)


@router.post("", response_model=NoteOut)
def create_note(data: NoteIn, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    row = Note(user_id=user.id, **{**data.model_dump(), "pinned": int(data.pinned)})
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_out(row)


@router.get("/{note_id}", response_model=NoteOut)
def get_note(note_id: int, user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    return _to_out(_get_owned(db, user, note_id))


@router.put("/{note_id}", response_model=NoteOut)
def update_note(note_id: int, data: NoteIn, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    row = _get_owned(db, user, note_id)
    for key, value in data.model_dump().items():
        setattr(row, key, int(value) if key == "pinned" else value)
    db.commit()
    db.refresh(row)
    return _to_out(row)


@router.delete("/{note_id}")
def delete_note(note_id: int, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    row = _get_owned(db, user, note_id)
    db.delete(row)
    db.commit()
    return {"ok": True}
