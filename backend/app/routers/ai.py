"""AI 接口：自然语言记账草稿、便签草稿、月度消费总结。

安全设计：草稿不直接落库，必须由用户确认后走 /api/bills 保存；
每次调用限流并写日志；输出经结构校验与脱敏。
"""
import time
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app import config
from app.deps import get_current_user, get_db
from app.models import Bill, BillCategory, User
from app.schemas import (
    AskIn, AskOut, BillDraft, CategoryStatItem, InsightOut, NoteDraft,
    ParseBillIn, ParseBillOut, ParseNoteIn, ParseNoteOut, SummaryOut,
)
from app.services import ai_service
from app.services.ai_service import (
    AIServiceError, PROMPT_VERSION, build_ask_step1_messages,
    build_ask_step2_messages, build_insight_messages, build_parse_bill_messages,
    build_parse_note_messages, build_summary_messages, check_rate_limit,
    ensure_configured, log_call, mask_sensitive,
)

router = APIRouter()


def _category_names(db: Session, user: User) -> list[str]:
    rows = db.scalars(select(BillCategory).where(
        (BillCategory.user_id.is_(None)) | (BillCategory.user_id == user.id))).all()
    names = sorted({r.name for r in rows})
    return names or ["其他"]


def _coerce_amount(value) -> Decimal | None:
    """金额容错转换：接受数字或"32元"这类字符串；无法确定时返回 None。"""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        amount = Decimal(str(round(float(value), 2)))
        return amount.quantize(Decimal("0.01")) if amount > 0 else None
    if isinstance(value, str):
        text = value.strip().replace("元", "").replace("块", "").replace("￥", "").replace("¥", "")
        try:
            amount = Decimal(text)
            return amount.quantize(Decimal("0.01")) if amount > 0 else None
        except InvalidOperation:
            return None
    return None


def _coerce_date(value) -> date | None:
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(value.strip()[:10], fmt).date()
            except ValueError:
                continue
    return None


def _validate_bill_drafts(data: dict, categories: list[str]) -> tuple[list[BillDraft], str]:
    """把模型 JSON 转成受控草稿：类型白名单、金额/日期校验、分类兜底、备注脱敏。"""
    raw_bills = data.get("bills")
    if not isinstance(raw_bills, list):
        raise AIServiceError(502, "AI 返回缺少 bills 数组，请重试或手动记账。")

    drafts: list[BillDraft] = []
    for item in raw_bills[:10]:  # 最多 10 条，防止异常输出
        if not isinstance(item, dict):
            continue
        bill_type = item.get("type") if item.get("type") in ("income", "expense") else "expense"
        amount = _coerce_amount(item.get("amount"))
        bill_date = _coerce_date(item.get("bill_date"))
        category = str(item.get("category") or "").strip()
        missing = [f for f in item.get("missing_fields", []) if isinstance(f, str)][:5]

        if not category or category not in categories:
            category = "其他"
            if "category" not in missing:
                missing.append("category")
        if amount is None and "amount" not in missing:
            missing.append("amount")
        if bill_date is None and "bill_date" not in missing:
            missing.append("bill_date")

        remark = mask_sensitive(str(item.get("remark") or "")[:200])
        drafts.append(BillDraft(
            type=bill_type, amount=amount, category=category,
            bill_date=bill_date, remark=remark, missing_fields=missing))

    notice = str(data.get("notice") or "")[:200]
    masked = any(
        mask_sensitive(str(item.get("remark") or "")[:200])
        != str(item.get("remark") or "")[:200]
        for item in raw_bills if isinstance(item, dict))
    if masked:
        notice = (notice + " 已检测到备注中的疑似敏感数字并自动脱敏，请勿在记账内容中提交密码等信息。").strip()[:200]
    # 一致性校验：已解析出草稿时，清除矛盾的“未识别”提示
    if drafts and "未识别到记账内容" in notice:
        notice = notice.replace("未识别到记账内容", "").strip()
    return drafts, notice


@router.post("/parse-bill", response_model=ParseBillOut)
async def parse_bill(req: ParseBillIn, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    ensure_configured()
    check_rate_limit(db, user.id)

    categories = _category_names(db, user)
    messages = build_parse_bill_messages(req.text, categories)
    retry_hint = (
        "你的上一次输出不是合法 JSON。请严格按照用户最后一次输入的文本重新输出："
        '只允许一个 JSON 对象，不要任何解释或 Markdown。注意：上面示例仅为格式参考，禁止照抄示例内容；'
        '如果用户输入与记账无关，必须返回 {"bills": [], "notice": "未识别到记账内容"}。')
    start = time.monotonic()
    try:
        data = await ai_service.chat_json(messages, retry_hint=retry_hint)
        drafts, notice = _validate_bill_drafts(data, categories)
        latency = int((time.monotonic() - start) * 1000)
        log_call(db, user_id=user.id, feature="parse_bill", status="success",
                 latency_ms=latency, input_chars=len(req.text))
        return ParseBillOut(drafts=drafts, notice=notice,
                            prompt_version=PROMPT_VERSION,
                            model=config.AI_MODEL, latency_ms=latency)
    except AIServiceError as exc:
        latency = int((time.monotonic() - start) * 1000)
        log_call(db, user_id=user.id, feature="parse_bill", status="error",
                 latency_ms=latency, input_chars=len(req.text),
                 error_msg=exc.message)
        if exc.kind == "format":
            # 两次都无法得到合法 JSON：按“未识别到记账内容”温和降级，提示用户换说法
            return ParseBillOut(
                drafts=[], notice="未能从这段文本中识别到记账内容，请换一种说法，或使用手动记账。",
                prompt_version=PROMPT_VERSION, model=config.AI_MODEL, latency_ms=latency)
        raise exc


@router.post("/parse-note", response_model=ParseNoteOut)
async def parse_note(req: ParseNoteIn, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    ensure_configured()
    check_rate_limit(db, user.id)

    messages = build_parse_note_messages(req.text, date.today().isoformat())
    retry_hint = (
        "你的上一次输出不是合法 JSON。请严格按照用户最后一次输入的文本重新输出："
        '只允许一个 JSON 对象，不要任何解释或 Markdown；禁止照抄示例内容；'
        '如果与便签无关，必须返回 {"title": "", "content": "", "note_type": "note", '
        '"due_at": null, "missing_fields": [], "notice": "未识别到便签内容"}。')
    start = time.monotonic()
    try:
        data = await ai_service.chat_json(messages, retry_hint=retry_hint)
        draft_data = data if "title" in data or "content" in data else {}
        if not draft_data:
            raise AIServiceError(502, "AI 未返回便签草稿，请重试或手动创建。", kind="format")
        due_at = None
        raw_due = draft_data.get("due_at")
        if isinstance(raw_due, str) and raw_due.strip():
            for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    due_at = datetime.strptime(raw_due.strip()[:16], fmt)
                    break
                except ValueError:
                    continue
        missing = [f for f in draft_data.get("missing_fields", []) if isinstance(f, str)][:5]
        if not draft_data.get("title"):
            missing = ["title"] + [m for m in missing if m != "title"]
        draft = NoteDraft(
            title=str(draft_data.get("title") or "")[:100],
            content=mask_sensitive(str(draft_data.get("content") or "")[:2000]),
            note_type=draft_data.get("note_type") if draft_data.get("note_type") in ("note", "todo") else "note",
            due_at=due_at, missing_fields=missing)
        latency = int((time.monotonic() - start) * 1000)
        log_call(db, user_id=user.id, feature="parse_note", status="success",
                 latency_ms=latency, input_chars=len(req.text))
        return ParseNoteOut(draft=draft, notice=str(data.get("notice") or "")[:200],
                            prompt_version=PROMPT_VERSION,
                            model=config.AI_MODEL, latency_ms=latency)
    except AIServiceError as exc:
        latency = int((time.monotonic() - start) * 1000)
        log_call(db, user_id=user.id, feature="parse_note", status="error",
                 latency_ms=latency, input_chars=len(req.text), error_msg=exc.message)
        if exc.kind == "format":
            return ParseNoteOut(
                draft=NoteDraft(), notice="未能从这段文本中整理出便签内容，请换一种说法，或手动创建。",
                prompt_version=PROMPT_VERSION, model=config.AI_MODEL, latency_ms=latency)
        raise exc


@router.get("/summary", response_model=SummaryOut)
async def summary(month: str = Query(default=""),
                  user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """月度消费总结：数据由后端 SQL 统计，模型只负责解释，避免编造数字。"""
    month = month or date.today().strftime("%Y-%m")
    year, mon = int(month[:4]), int(month[5:7])
    month_condition = [
        Bill.user_id == user.id,
        extract("year", Bill.bill_date) == year,
        extract("month", Bill.bill_date) == mon,
    ]
    income = Decimal(str(db.scalar(select(func.coalesce(func.sum(Bill.amount), 0)).where(
        *month_condition, Bill.type == "income")) or 0))
    expense = Decimal(str(db.scalar(select(func.coalesce(func.sum(Bill.amount), 0)).where(
        *month_condition, Bill.type == "expense")) or 0))
    top_rows = db.execute(
        select(BillCategory.name, func.sum(Bill.amount))
        .join(Bill, Bill.category_id == BillCategory.id)
        .where(*month_condition, Bill.type == "expense")
        .group_by(BillCategory.name)
        .order_by(func.sum(Bill.amount).desc()).limit(5)).all()
    top_categories = [
        CategoryStatItem(category=name, amount=Decimal(str(amount)), ratio=0.0)
        for name, amount in top_rows]

    if income == 0 and expense == 0:
        # 无数据时不调用模型，直接给出确定提示（成本控制 + 防幻觉）
        return SummaryOut(
            month=month, income=income, expense=expense, net=income - expense,
            top_categories=top_categories,
            summary=f"{month} 月暂无账单数据，请先记录收支后再生成分析。",
            notice="未调用 AI：本月无数据。",
            prompt_version=PROMPT_VERSION, model=config.AI_MODEL or "-")

    ensure_configured()
    check_rate_limit(db, user.id)
    stats = {"income": income, "expense": expense,
             "net": income - expense,
             "top_categories": [{"category": c.category, "amount": c.amount}
                                for c in top_categories]}
    messages = build_summary_messages(month, stats)
    start = time.monotonic()
    try:
        data = await ai_service.chat_json(messages, temperature=0.3)
        text = str(data.get("summary") or "").strip()[:500]
        if not text:
            raise AIServiceError(502, "AI 未返回分析内容，请重试。")
        latency = int((time.monotonic() - start) * 1000)
        log_call(db, user_id=user.id, feature="summary", status="success",
                 latency_ms=latency, input_chars=len(month))
        return SummaryOut(
            month=month, income=income, expense=expense, net=income - expense,
            top_categories=top_categories, summary=text,
            notice="分析由 AI 基于真实统计数据生成，仅供参考。",
            prompt_version=PROMPT_VERSION, model=config.AI_MODEL)
    except AIServiceError as exc:
        latency = int((time.monotonic() - start) * 1000)
        log_call(db, user_id=user.id, feature="summary", status="error",
                 latency_ms=latency, input_chars=len(month), error_msg=exc.message)
        raise exc


# ---------------- 首页一句话洞察 ----------------

# 进程内当日缓存：同一用户同一天只调用一次模型（成本控制）
_INSIGHT_CACHE: dict[int, tuple[str, str]] = {}


def _shift_month(month: str, delta: int) -> str:
    year, mon = int(month[:4]), int(month[5:7]) + delta
    if mon < 1:
        year, mon = year - 1, 12
    elif mon > 12:
        year, mon = year + 1, 1
    return f"{year:04d}-{mon:02d}"


def _month_condition(user_id: int, month: str):
    return [
        Bill.user_id == user_id,
        extract("year", Bill.bill_date) == int(month[:4]),
        extract("month", Bill.bill_date) == int(month[5:7]),
    ]


def _global_stats(db: Session, user_id: int, month: str) -> dict:
    cond = _month_condition(user_id, month)
    income = Decimal(str(db.scalar(select(func.coalesce(func.sum(Bill.amount), 0))
                                    .where(*cond, Bill.type == "income")) or 0))
    expense = Decimal(str(db.scalar(select(func.coalesce(func.sum(Bill.amount), 0))
                                     .where(*cond, Bill.type == "expense")) or 0))
    count = db.scalar(select(func.count()).where(*cond)) or 0
    top_rows = db.execute(
        select(BillCategory.name, func.sum(Bill.amount))
        .join(Bill, Bill.category_id == BillCategory.id)
        .where(*cond, Bill.type == "expense")
        .group_by(BillCategory.name)
        .order_by(func.sum(Bill.amount).desc()).limit(3)).all()
    return {
        "income": income, "expense": expense, "net": income - expense, "count": count,
        "top_categories": [{"category": n, "amount": Decimal(str(a))} for n, a in top_rows],
    }


@router.get("/insight", response_model=InsightOut)
async def insight(refresh: bool = False, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """首页 AI 洞察：当日只调用一次模型；无数据或 AI 不可用时返回规则文案。"""
    today = date.today()
    month = today.strftime("%Y-%m")
    cached = _INSIGHT_CACHE.get(user.id)
    if cached and cached[0] == today.isoformat() and not refresh:
        return InsightOut(text=cached[1], month=month, cached=True,
                          model=config.AI_MODEL or "")

    stats = _global_stats(db, user.id, month)
    rule_text = (f"本月已支出 ¥{stats['expense']}，共 {stats['count']} 笔，"
                 f"继续记账可以看清消费结构")
    if stats["count"] == 0:
        text = "本月还没有账单，用一句话就能记一笔，试试 AI 记账吧"
        _INSIGHT_CACHE[user.id] = (today.isoformat(), text)
        return InsightOut(text=text, month=month, notice="本月暂无数据，未调用 AI")

    try:
        ensure_configured()
        check_rate_limit(db, user.id)
    except AIServiceError:
        return InsightOut(text=rule_text, month=month,
                          notice="AI 未启用或次数已用完，当前为基础提示")

    start = time.monotonic()
    try:
        data = await ai_service.chat_json(
            build_insight_messages(month, stats),
            retry_hint='你的上一次输出不是合法 JSON。请只输出 {"insight": "一句话"} 形式的 JSON 对象。')
        text = str(data.get("insight") or "").strip()[:150]
        if not text:
            raise AIServiceError(502, "AI 未返回洞察内容", kind="format")
        latency = int((time.monotonic() - start) * 1000)
        log_call(db, user_id=user.id, feature="insight", status="success",
                 latency_ms=latency, input_chars=0)
        _INSIGHT_CACHE[user.id] = (today.isoformat(), text)
        return InsightOut(text=text, month=month, model=config.AI_MODEL)
    except AIServiceError as exc:
        latency = int((time.monotonic() - start) * 1000)
        log_call(db, user_id=user.id, feature="insight", status="error",
                 latency_ms=latency, input_chars=0, error_msg=exc.message)
        return InsightOut(text=rule_text, month=month,
                          notice="AI 暂时不可用，当前为基础提示")


# ---------------- 问账本（工具调用） ----------------

_ASK_TOOLS = {"monthly_summary", "category_summary", "top_categories", "largest_bill"}


def _execute_ask_tool(db: Session, user: User, tool: str, params: dict) -> dict:
    """执行模型选择的查询工具，只返回当前用户的聚合数据（不返回明细隐私）。"""
    this_month = date.today().strftime("%Y-%m")
    month = this_month if str(params.get("month") or "this") == "this" \
        else _shift_month(this_month, -1)
    cond = _month_condition(user.id, month)

    if tool == "monthly_summary":
        stats = _global_stats(db, user.id, month)
        return {"month": month, "income": str(stats["income"]),
                "expense": str(stats["expense"]), "net": str(stats["net"]),
                "count": stats["count"]}
    if tool == "category_summary":
        name = str(params.get("category") or "").strip()
        cat = db.scalar(select(BillCategory).where(
            BillCategory.name == name,
            (BillCategory.user_id.is_(None)) | (BillCategory.user_id == user.id)).limit(1))
        if cat is None:
            return {"month": month, "category": name, "found": False,
                    "message": "分类不存在"}
        amount = db.scalar(select(func.coalesce(func.sum(Bill.amount), 0))
                           .where(*cond, Bill.category_id == cat.id)) or 0
        count = db.scalar(select(func.count())
                          .where(*cond, Bill.category_id == cat.id)) or 0
        return {"month": month, "category": name, "found": True,
                "amount": str(Decimal(str(amount))), "count": count}
    if tool == "top_categories":
        try:
            n = max(1, min(int(params.get("n") or 3), 5))
        except (TypeError, ValueError):
            n = 3
        rows = db.execute(
            select(BillCategory.name, func.sum(Bill.amount))
            .join(Bill, Bill.category_id == BillCategory.id)
            .where(*cond, Bill.type == "expense")
            .group_by(BillCategory.name)
            .order_by(func.sum(Bill.amount).desc()).limit(n)).all()
        return {"month": month,
                "items": [{"category": name, "amount": str(Decimal(str(a)))}
                          for name, a in rows]}
    if tool == "largest_bill":
        row = db.scalar(select(Bill).where(*cond, Bill.type == "expense")
                        .order_by(Bill.amount.desc()).limit(1))
        if row is None:
            return {"month": month, "found": False}
        cat = db.get(BillCategory, row.category_id) if row.category_id else None
        return {"month": month, "found": True, "amount": str(row.amount),
                "category": cat.name if cat else "未分类",
                "bill_date": row.bill_date.isoformat(), "remark": row.remark}
    return {"error": "不支持的工具"}


@router.post("/ask", response_model=AskOut)
async def ask(req: AskIn, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    """问账本：模型规划查询 → 后端执行 → 模型组织回答（多步任务可追踪）。"""
    ensure_configured()
    check_rate_limit(db, user.id)

    month = date.today().strftime("%Y-%m")
    categories = _category_names(db, user)
    start = time.monotonic()
    try:
        plan = await ai_service.chat_json(
            build_ask_step1_messages(req.question, month, categories),
            retry_hint='只输出 {"tool": "工具名", "params": {}} 形式的 JSON 对象。')
        tool = str(plan.get("tool") or "unsupported")
        params = plan.get("params") if isinstance(plan.get("params"), dict) else {}
        steps = ["理解问题并选择查询工具"]

        if tool not in _ASK_TOOLS:
            answer = ("这个问题我还回答不了。可以试试问我：本月收支多少、"
                      "某个分类花了多少、最大的支出是什么。")
            latency = int((time.monotonic() - start) * 1000)
            log_call(db, user_id=user.id, feature="ask", status="success",
                     latency_ms=latency, input_chars=len(req.question))
            return AskOut(answer=answer, tool="unsupported", steps=steps,
                          prompt_version=PROMPT_VERSION, model=config.AI_MODEL,
                          latency_ms=latency)

        result = _execute_ask_tool(db, user, tool, params)
        steps.append(f"执行数据查询（{tool}）")

        data = await ai_service.chat_json(
            build_ask_step2_messages(req.question, tool, params, result),
            retry_hint='只输出 {"answer": "回答内容"} 形式的 JSON 对象。')
        answer = str(data.get("answer") or "").strip()[:200]
        if not answer:
            raise AIServiceError(502, "AI 未返回回答，请重试。", kind="format")
        steps.append("基于查询结果生成回答")

        latency = int((time.monotonic() - start) * 1000)
        log_call(db, user_id=user.id, feature="ask", status="success",
                 latency_ms=latency, input_chars=len(req.question))
        return AskOut(answer=answer, tool=tool, tool_params=params,
                      data_used=result, steps=steps,
                      prompt_version=PROMPT_VERSION, model=config.AI_MODEL,
                      latency_ms=latency)
    except AIServiceError as exc:
        latency = int((time.monotonic() - start) * 1000)
        log_call(db, user_id=user.id, feature="ask", status="error",
                 latency_ms=latency, input_chars=len(req.question),
                 error_msg=exc.message)
        raise exc
