"""
데이터베이스 설정 파일.

- SQLite 파일 하나(idea_gateway.db)에 모든 데이터를 저장한다.
- 초보자용으로 별도 DB 서버 설치가 필요 없다.
- SQLModel은 FastAPI 제작자가 만든 도구로, SQLAlchemy를 더 쉽게 쓰게 해준다.
"""
from sqlmodel import SQLModel, create_engine, Session

# sqlite:///./파일이름  → 현재 폴더에 DB 파일이 생긴다.
DATABASE_URL = "sqlite:///./idea_gateway.db"

# check_same_thread=False : FastAPI가 여러 요청을 처리할 때 필요한 설정.
engine = create_engine(
    DATABASE_URL,
    echo=False,  # True로 바꾸면 실행되는 SQL이 콘솔에 다 찍힌다(학습용).
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """테이블이 없으면 만든다. 서버 시작 시 한 번 호출한다."""
    # models를 import 해야 SQLModel이 어떤 테이블을 만들지 알 수 있다.
    import app.models  # noqa: F401
    SQLModel.metadata.create_all(engine)
    _add_missing_columns()


def _add_missing_columns() -> None:
    """
    이미 만들어진 SQLite 파일에 새 컬럼이 없으면 추가한다.
    create_all()은 없는 '테이블'만 만들어주고, 기존 테이블에 컬럼을 추가해주지는 않기 때문.
    (예: 툴 포이즈닝 탐지를 위해 tool 테이블에 description/baseline_description을 나중에 추가한 경우)
    """
    with engine.connect() as conn:
        existing = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(tool)").fetchall()}
        if "description" not in existing:
            conn.exec_driver_sql("ALTER TABLE tool ADD COLUMN description TEXT DEFAULT ''")
        if "baseline_description" not in existing:
            conn.exec_driver_sql("ALTER TABLE tool ADD COLUMN baseline_description TEXT")
        conn.commit()


def get_session():
    """
    요청 하나마다 DB 세션을 열어주고, 끝나면 자동으로 닫는다.
    FastAPI의 Depends()와 함께 쓰는 '의존성' 함수다.
    """
    with Session(engine) as session:
        yield session
