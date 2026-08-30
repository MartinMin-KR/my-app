import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# .env 파일을 읽어서 환경변수로 올린다. 이걸 해야 os.getenv 로 꺼낼 수 있다
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# engine = 데이터베이스와 실제로 연결되는 통로
# check_same_thread=False 는 SQLite 전용 옵션. FastAPI 가 요청마다 다른 스레드를 쓸 수 있어서 필요
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SessionLocal() 을 부르면 세션(작업 단위) 하나가 생긴다
# 세션을 통해 값을 넣고, 읽고, 마지막에 commit 한다
SessionLocal = sessionmaker(bind=engine)


# 모든 표 클래스가 상속받는 부모. models.py 의 클래스들이 이걸 물려받는다
class Base(DeclarativeBase):
    pass
