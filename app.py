from datetime import date

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from database import SessionLocal
from models import Expense

# FastAPI 앱 객체. uvicorn app:app 의 뒤쪽 "app"이 바로 이 변수다
app = FastAPI()

# static/ 폴더 안의 파일(css, js, 이미지)을 /static 주소로 그대로 내보낸다
app.mount("/static", StaticFiles(directory="static"), name="static")

# templates/ 폴더의 HTML 파일을 Jinja2로 읽어서 완성하는 도구
templates = Jinja2Templates(directory="templates")


# 주소 "/" 로 GET 요청이 오면 이 함수가 실행된다
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    # DB 에서 고정비 전부 읽어오기. 결제일 순으로 정렬
    # with 블록이 끝나면 세션이 자동으로 닫힌다
    with SessionLocal() as db:
        expenses = db.scalars(
            select(Expense).order_by(Expense.billing_day)
        ).all()

    # 요약 두 줄 계산
    today_day = date.today().day  # 오늘이 며칠인지 (예: 30)
    total = sum(e.amount for e in expenses)  # 전체 월 합계
    remaining = sum(
        e.amount for e in expenses if e.billing_day >= today_day
    )  # 결제일이 아직 안 지난 것(오늘 포함)의 합 = 이번 달 남은 금액

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
        },
    )


# 폼이 제출되면 "/expenses" 로 POST 요청이 온다. GET(달라) 이 아니라 POST(보낸다)
# Form(...) 은 "폼에서 이 이름으로 보낸 값을 받아라". 이걸 위해 python-multipart 가 필요하다
@app.post("/expenses")
def create_expense(
    name: str = Form(...),
    amount: int = Form(...),
    billing_day: int = Form(...),
    memo: str = Form(""),  # 기본값 "" = 안 보내도 됨 (선택 입력)
):
    # 받은 값으로 Expense 객체를 만들어 DB 에 넣는다 (③에서 터미널로 한 것과 같은 코드)
    # 메모가 빈 문자열이면 None(비어있음)으로 저장
    with SessionLocal() as db:
        db.add(Expense(
            name=name,
            amount=amount,
            billing_day=billing_day,
            memo=memo.strip() or None,
        ))
        db.commit()

    # 저장 후 첫 화면("/")으로 돌려보낸다. 303 은 "POST 끝났으니 GET 으로 저기 가라"는 뜻
    return RedirectResponse(url="/", status_code=303)


# 주소를 하나 더. "/about" 으로 오면 이 함수가 실행된다
# HTML 파일 없이 문자열만 돌려줘도 브라우저에 그대로 보인다
@app.get("/about")
def about():
    return {"app": "월 고정비 정리", "stack": "FastAPI + Jinja2 + SQLite"}
