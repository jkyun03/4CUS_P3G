"""
SQLite 연결, 테이블 생성, 요청별 DB 세션 제공.
"""
from sqlmodel import SQLModel, create_engine, Session


DATABASE_URL = "sqlite:///./idea_gateway.db"


engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    import app.models
    SQLModel.metadata.create_all(engine)
    _add_missing_columns()


def _add_missing_columns() -> None:
    with engine.connect() as conn:
        existing = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(tool)").fetchall()}
        if "description" not in existing:
            conn.exec_driver_sql("ALTER TABLE tool ADD COLUMN description TEXT DEFAULT ''")
        if "baseline_description" not in existing:
            conn.exec_driver_sql("ALTER TABLE tool ADD COLUMN baseline_description TEXT")
        conn.commit()

        tc_existing = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(toolcall)").fetchall()}
        if "user_id" not in tc_existing:
            conn.exec_driver_sql("ALTER TABLE toolcall ADD COLUMN user_id TEXT DEFAULT ''")
        conn.commit()


def get_session():
    with Session(engine) as session:
        yield session
