"""
실제 MCP 서버에 연결된 직후, 그 서버가 제공하는 도구들을 Tool 테이블에 등록한다.

등록 안 된 도구는 tool_call.py 의 권한 검사에서 무조건 차단되므로 필요한 단계다.
안전을 위해 기본값은 가장 보수적으로 넣는다: enabled=False, system_admin만 허용.
실제로 쓸 도구는 관리자가 Tools 화면(PATCH /tools/{name})에서 검토 후 켜야 한다.
"""
from sqlmodel import Session, select

from app.database import engine
from app.models import Tool
from app.mcp_tools.mcp_client import mcp_client


async def sync_real_tools() -> None:
    if not mcp_client.connected:
        return
    real_tools = await mcp_client.list_tools()
    with Session(engine) as session:
        for t in real_tools:
            exists = session.exec(select(Tool).where(Tool.name == t["name"])).first()
            if not exists:
                session.add(Tool(
                    name=t["name"],
                    role=(t.get("description") or "")[:50] or "실제 MCP 도구",
                    base_risk="high",
                    enabled=False,
                    allowed_roles=["system_admin"],
                ))
        session.commit()
