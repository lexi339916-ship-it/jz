"""SQLAlchemy ORM 模型，与 database/schema.sql 保持一致。"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    CHAR, BigInteger, Date, DateTime, DECIMAL, Enum, Index, Integer,
    String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# 主键类型：MySQL 用 BIGINT；SQLite 需要 INTEGER 才能自增
PKType = BigInteger().with_variant(Integer, "sqlite")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)


class BillCategory(Base):
    __tablename__ = "bill_categories"
    __table_args__ = (UniqueConstraint("user_id", "name", "type", name="uq_category_user_name_type"),)

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    # user_id 为 NULL 表示系统预置分类，所有用户可见；非空表示用户自定义
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    type: Mapped[str] = mapped_column(Enum("income", "expense"), nullable=False)


class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    type: Mapped[str] = mapped_column(Enum("income", "expense"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    bill_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    remark: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    # 数据来源可追溯：manual=手动录入，ai=AI 草稿经用户确认后保存
    source: Mapped[str] = mapped_column(String(10), nullable=False, default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (Index("idx_bill_user_date", "user_id", "bill_date"),)


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    note_type: Mapped[str] = mapped_column(Enum("note", "todo"), nullable=False, default="note")
    status: Mapped[str] = mapped_column(Enum("open", "done"), nullable=False, default="open")
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (Index("idx_note_user_status", "user_id", "status"),)


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("user_id", "month", name="uq_budget_user_month"),)

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    month: Mapped[str] = mapped_column(CHAR(7), nullable=False)  # 格式：2026-10
    amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)


class AICallLog(Base):
    """AI 调用日志：保留功能、提示词版本、模型、耗时与结果，满足可复现要求。"""
    __tablename__ = "ai_call_logs"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    feature: Mapped[str] = mapped_column(String(30), nullable=False)   # parse_bill / parse_note / summary
    prompt_version: Mapped[str] = mapped_column(String(10), nullable=False)
    model: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)   # success / error / limited
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_msg: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    input_chars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (Index("idx_ai_log_user_date", "user_id", "created_at"),)
