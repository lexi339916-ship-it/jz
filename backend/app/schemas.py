"""接口出入参契约（Pydantic）。"""
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------- 认证 ----------

class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=20, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=6, max_length=32)
    nickname: str = Field(default="", max_length=30)


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=20)
    password: str = Field(min_length=1, max_length=32)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    nickname: str
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdateIn(BaseModel):
    nickname: str = Field(default="", max_length=30)
    old_password: str = Field(default="", max_length=32)
    new_password: str = Field(default="", max_length=32)


# ---------- 分类 ----------

class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    type: Literal["income", "expense"]


class CategoryOut(BaseModel):
    id: int
    name: str
    type: str
    is_system: bool


# ---------- 账单 ----------

class BillIn(BaseModel):
    type: Literal["income", "expense"]
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category: str = Field(min_length=1, max_length=40)
    bill_date: date
    remark: str = Field(default="", max_length=200)
    # manual=手动录入；ai=AI 草稿确认后保存；receipt=截图识别确认后保存（可追溯）
    source: Literal["manual", "ai", "receipt"] = "manual"
    pay_channel: str = Field(default="", max_length=20)
    funding_account: str = Field(default="", max_length=40)


class BillOut(BaseModel):
    id: int
    type: str
    amount: Decimal
    category: str
    category_id: int | None
    bill_date: date
    remark: str
    source: str
    pay_channel: str
    funding_account: str
    created_at: datetime


class BillPageOut(BaseModel):
    items: list[BillOut]
    total: int
    page: int
    page_size: int


# ---------- 便签 ----------

class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(default="", max_length=5000)
    note_type: Literal["note", "todo"] = "note"
    status: Literal["open", "done"] = "open"
    due_at: datetime | None = None
    priority: Literal["high", "medium", "low"] = "medium"
    pinned: bool = False
    color: str = Field(default="lilac", max_length=20)


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    content: str
    note_type: str
    status: str
    due_at: datetime | None
    priority: str
    pinned: bool
    color: str
    is_overdue: bool
    created_at: datetime
    updated_at: datetime


class NotePageOut(BaseModel):
    items: list[NoteOut]
    total: int
    pending_count: int


# ---------- 预算 ----------

class BudgetIn(BaseModel):
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class BudgetOut(BaseModel):
    month: str
    amount: Decimal
    spent: Decimal
    remaining: Decimal
    usage_ratio: float  # 0~1，已用比例


# ---------- 统计 ----------

class DayPoint(BaseModel):
    date: date
    expense: Decimal
    income: Decimal


class MonthlyStatsOut(BaseModel):
    month: str
    income: Decimal
    expense: Decimal
    net: Decimal
    count: int
    days: list[DayPoint]


class CategoryStatItem(BaseModel):
    category: str
    amount: Decimal
    ratio: float


class CategoryStatsOut(BaseModel):
    month: str
    type: str
    total: Decimal
    items: list[CategoryStatItem]


class ChannelStatItem(BaseModel):
    channel: str
    amount: Decimal
    count: int
    ratio: float


class ChannelStatsOut(BaseModel):
    month: str          # 空字符串表示全部时间
    type: str
    total: Decimal
    items: list[ChannelStatItem]


class ProfileStatsOut(BaseModel):
    """个人中心统计卡片数据。"""
    total_bills: int
    total_days: int
    total_notes: int
    pending_todos: int


# ---------- 储蓄目标 ----------

class GoalIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    target_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class GoalDepositIn(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class GoalOut(BaseModel):
    id: int
    name: str
    target_amount: Decimal
    saved_amount: Decimal
    remaining: Decimal
    progress_ratio: float          # 0~1（可超 1）
    estimated_finish: str | None    # 按近 3 个月平均月结余估算
    avg_monthly_net: Decimal


# ---------- 生活挑战 ----------

class ChallengeIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    category: str = Field(min_length=1, max_length=40)
    period_days: Literal[7, 30] = 7
    target_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class ChallengeOut(BaseModel):
    id: int
    name: str
    category: str
    period_days: int
    target_amount: Decimal
    start_date: date
    end_date: date
    current_spend: Decimal
    previous_spend: Decimal | None   # 上一个同长度周期的支出
    change_pct: float | None         # 环比变化百分比
    progress_ratio: float            # 当前已花 / 上限
    status: str                      # on_track / over / finished / failed
    days_left: int


# ---------- AI ----------

class ParseBillIn(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class BillDraft(BaseModel):
    """AI 生成的账单草稿：仅候选数据，必须经用户核对确认后才可保存。"""
    type: Literal["income", "expense"] = "expense"
    amount: Decimal | None = None
    category: str = "其他"
    bill_date: date | None = None
    remark: str = ""
    missing_fields: list[str] = Field(default_factory=list)


class ParseBillOut(BaseModel):
    drafts: list[BillDraft]
    notice: str = ""
    prompt_version: str
    model: str
    latency_ms: int


class ParseNoteIn(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class NoteDraft(BaseModel):
    title: str = ""
    content: str = ""
    note_type: Literal["note", "todo"] = "note"
    due_at: datetime | None = None
    priority: Literal["high", "medium", "low"] = "medium"
    missing_fields: list[str] = Field(default_factory=list)


class ParseNoteOut(BaseModel):
    drafts: list[NoteDraft]
    notice: str = ""
    prompt_version: str
    model: str
    latency_ms: int


class ReceiptDraft(BaseModel):
    """截图识别出的账单草稿：字段缺失一律标记待确认，不猜测。"""
    type: Literal["income", "expense"] = "expense"
    amount: Decimal | None = None
    merchant: str = ""
    category: str = "其他"
    bill_date: date | None = None
    bill_time: str = ""
    remark: str = ""
    status: Literal["success", "pending", "refunded", "failed", "unknown"] = "unknown"
    pay_channel: str = ""
    funding_account: str = ""
    missing_fields: list[str] = Field(default_factory=list)
    duplicate_suspect: bool = False
    duplicate_hint: str = ""


class ParseReceiptOut(BaseModel):
    found: bool = True
    drafts: list[ReceiptDraft]
    notice: str = ""
    prompt_version: str
    model: str
    latency_ms: int


class SummaryOut(BaseModel):
    month: str
    income: Decimal
    expense: Decimal
    net: Decimal
    top_categories: list[CategoryStatItem]
    summary: str
    notice: str
    prompt_version: str
    model: str


class InsightOut(BaseModel):
    """首页 AI 洞察：一句话消费提示（当日缓存，失败时规则降级）。"""
    text: str
    month: str
    cached: bool = False
    model: str = ""
    notice: str = ""


class AskIn(BaseModel):
    question: str = Field(min_length=2, max_length=200)


class AskOut(BaseModel):
    """问账本：模型选择查询工具 → 后端执行 → 生成回答（多步任务可追踪）。"""
    answer: str
    tool: str = ""
    tool_params: dict = Field(default_factory=dict)
    data_used: dict = Field(default_factory=dict)
    steps: list[str] = Field(default_factory=list)
    prompt_version: str
    model: str
    latency_ms: int
