from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


# 고정비 표. 클래스 하나 = 표 하나, 속성 하나 = 열 하나
class Expense(Base):
    __tablename__ = "expenses"  # 실제 DB 안에서의 표 이름

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # 자동으로 1, 2, 3... 붙는 번호
    name: Mapped[str] = mapped_column(String(100))              # 이름 (예: 월세)
    amount: Mapped[int] = mapped_column(Integer)                # 금액 (원)
    billing_day: Mapped[int] = mapped_column(Integer)           # 결제일 (매월 며칠, 1~31)
    memo: Mapped[str | None] = mapped_column(String(200), nullable=True)  # 메모. 비워도 됨 (나중에 추가한 열)
    # soft delete 용. 비어있으면(NULL) 살아있는 항목, 시각이 있으면 그때 삭제된 항목
    # is_deleted(예/아니오) 대신 시각을 남긴 이유: 달별 내역을 보려면 "언제" 지웠는지 필요 (결정_기록.md)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
