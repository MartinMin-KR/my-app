import calendar
from datetime import date, datetime, timedelta

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select

from database import SessionLocal
from models import Expense

# FastAPI 앱 객체. uvicorn app:app 의 뒤쪽 "app"이 바로 이 변수다
app = FastAPI()

# static/ 폴더 안의 파일(css, js, 이미지)을 /static 주소로 그대로 내보낸다
app.mount("/static", StaticFiles(directory="static"), name="static")

# templates/ 폴더의 HTML 파일을 Jinja2로 읽어서 완성하는 도구
templates = Jinja2Templates(directory="templates")


def billing_date_in(year: int, month: int, billing_day: int) -> date:
    # 그 달의 결제일 날짜를 만든다. 결제일이 그 달에 없으면(2월의 31일) 말일로 당긴다
    # — 실제 구독 서비스들의 표준 동작 (결정_기록.md)
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(billing_day, last_day))


def billed_in_month(e: Expense, year: int, month: int) -> bool:
    # "그 달에 돈이 나갔나" 판정: 그 달의 결제일 시점에 살아있었으면 나간 것 (결정_기록.md)
    if e.start_date is None:
        return False  # 시작일을 아직 안 채운 항목은 판정 불가 → 제외 (UPDATE 로 채울 것)
    bd = billing_date_in(year, month, e.billing_day)
    started = e.start_date <= bd                 # 결제일 전에 시작했고
    not_yet_deleted = e.deleted_at is None or e.deleted_at.date() > bd  # 결제일까지 살아있었다
    return started and not_yet_deleted


# 주소 "/" 로 GET 요청이 오면 이 함수가 실행된다
# ?month=2026-07 처럼 달을 지정하면 그 달의 지출 기록을 읽기 전용으로 보여준다
@app.get("/", response_class=HTMLResponse)
def index(request: Request, month: str | None = None):
    # DB 에서 고정비 전부 읽어오기. 결제일 순으로 정렬
    # with 블록이 끝나면 세션이 자동으로 닫힌다
    today = date.today()
    current_first = today.replace(day=1)  # 이번 달 1일 (달 비교용)

    # ?month=2026-07 파라미터 해석. 없거나 이상한 값이면 이번 달로
    try:
        selected = datetime.strptime(month, "%Y-%m").date() if month else current_first
    except ValueError:
        selected = current_first
    past_mode = selected != current_first  # 이번 달이 아니면 과거(읽기 전용) 모드

    with SessionLocal() as db:
        if past_mode:
            # 과거 달: 지운 것 포함 전부 꺼내서, "그 달 결제일에 살아있었나"로 거른다
            all_rows = db.scalars(select(Expense).order_by(Expense.billing_day)).all()
            expenses = [e for e in all_rows if billed_in_month(e, selected.year, selected.month)]
        else:
            # 이번 달: 살아있는 항목만 (기존 그대로)
            expenses = db.scalars(
                select(Expense)
                .where(Expense.deleted_at.is_(None))
                .order_by(Expense.billing_day)
            ).all()

        # 드롭다운에 넣을 달 목록: 가장 이른 시작일의 달부터 이번 달까지, 최신순
        earliest = db.scalar(select(func.min(Expense.start_date))) or current_first
        months = []
        m = current_first
        while m >= earliest.replace(day=1):
            months.append({"value": m.strftime("%Y-%m"), "label": f"{m.year}년 {m.month}월"})
            # 한 달 전으로 (1월이면 작년 12월로)
            m = (m.replace(day=1) - timedelta(days=1)).replace(day=1)

    total = sum(e.amount for e in expenses)  # 전체 월 합계 (과거 달이면 = 그 달 나간 돈)
    today_day = today.day
    remaining = sum(e.amount for e in expenses if e.billing_day >= today_day)  # 이번 달 남은 금액

    # index.html 에 파이썬 값들을 끼워넣어 응답으로 보낸다
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "월 고정비 정리",
            "expenses": expenses,
            "total": total,
            "remaining": remaining,
            "today_day": today_day,
            "today_iso": today.isoformat(),          # 폼 시작일 기본값 (예: 2026-09-06)
            "past_mode": past_mode,
            "selected_value": selected.strftime("%Y-%m"),
            "selected_label": f"{selected.year}년 {selected.month}월",
            "months": months,
        },
    )


# 폼이 제출되면 "/expenses" 로 POST 요청이 온다. GET(달라) 이 아니라 POST(보낸다)
# Form(...) 은 "폼에서 이 이름으로 보낸 값을 받아라". 이걸 위해 python-multipart 가 필요하다
@app.post("/expenses")
def create_expense(
    name: str = Form(...),
    amount: int = Form(...),
    billing_day: int = Form(...),
    start_date: date = Form(...),  # 구독 시작일. 필수 (폼에는 오늘이 기본값으로 채워져 있음)
    memo: str = Form(""),  # 기본값 "" = 안 보내도 됨 (선택 입력)
):
    # 받은 값으로 Expense 객체를 만들어 DB 에 넣는다 (③에서 터미널로 한 것과 같은 코드)
    # 메모가 빈 문자열이면 None(비어있음)으로 저장
    with SessionLocal() as db:
        db.add(Expense(
            name=name,
            amount=amount,
            billing_day=billing_day,
            start_date=start_date,
            memo=memo.strip() or None,
        ))
        db.commit()

    # 저장 후 첫 화면("/")으로 돌려보낸다. 303 은 "POST 끝났으니 GET 으로 저기 가라"는 뜻
    return RedirectResponse(url="/", status_code=303)


# 삭제. {expense_id} 는 빈칸 주소 — 이 자리에 온 값이 expense_id 로 들어온다
# 폼이 아니라 JS 의 fetch 가 DELETE 방식으로 보낸다 (index 쪽 main.js 참고)
@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):
    with SessionLocal() as db:
        expense = db.get(Expense, expense_id)  # 번호로 한 줄 꺼내기 (없으면 None)
        if expense is None:
            # 없는 번호면 404 로 거절 (이미 지워진 걸 또 지우는 경우 등)
            raise HTTPException(status_code=404, detail="해당 항목이 없습니다")
        # 줄을 지우지 않고 "지금 지워짐" 도장만 찍는다 (soft delete)
        expense.deleted_at = datetime.now()
        db.commit()
    # 받는 쪽이 사람이 아니라 JS 라서, HTML 대신 간단한 신호만 돌려준다
    return {"ok": True}


# 주소를 하나 더. "/about" 으로 오면 이 함수가 실행된다
# HTML 파일 없이 문자열만 돌려줘도 브라우저에 그대로 보인다
@app.get("/about")
def about():
    return {"app": "월 고정비 정리", "stack": "FastAPI + Jinja2 + SQLite"}
