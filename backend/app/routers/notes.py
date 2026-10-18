"""便签与待办接口：CRUD、搜索、状态切换。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Note, User
from app.schemas import NoteIn, NoteOut, NotePageOut

router = APIRouter()


def _to_out(row: Note) -> NoteOut:
    return NoteOut.model_validate(row)


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

    total = db.scalar(select(func.count()).where(*conditions)) or 0
    pending = db.scalar(select(func.count()).where(
        Note.user_id == user.id, Note.note_type == "todo", Note.status == "open")) or 0
    rows = db.scalars(
        select(Note).where(*conditions)
        .order_by(Note.updated_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    return NotePageOut(items=[_to_out(r) for r in rows], total=total, pending_count=pending)


@router.post("", response_model=NoteOut)
def create_note(data: NoteIn, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    row = Note(user_id=user.id, **data.model_dump())
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
        setattr(row, key, value)
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
