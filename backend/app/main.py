"""
FastAPI 앱 진입점.

실행: (backend 폴더에서)
    uvicorn app.main:app --reload

그러면 http://127.0.0.1:8000/docs 에서 API를 눌러가며 테스트할 수 있다.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.seed import seed_tools
from app.mcp_tools.mcp_client import mcp_client
from app.mcp_tools.sync import sync_real_tools
from app.api.tool_call import router as tool_call_router
from app.api.approval import router as approvals_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.events import router as events_router
from app.api.analytics import router as analytics_router
from app.api.tools import router as tools_router
from app.api.reports import router as reports_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시: 테이블 생성 + 초기 도구 목록 삽입
    init_db()
    seed_tools()
    try:
        await mcp_client.connect()
        await sync_real_tools()
    except Exception as e:
        print(f"[MCP] 실제 서버 연결 실패, mock으로 동작: {e}")
    yield
    await mcp_client.disconnect()


app = FastAPI(title="IDEA Gateway", version="0.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(tool_call_router)
app.include_router(approvals_router)
app.include_router(events_router)
app.include_router(analytics_router)
app.include_router(tools_router)
app.include_router(reports_router)

@app.get("/")
def root():
    return {"service": "IDEA Gateway", "docs": "http://127.0.0.1:8000/docs"}
