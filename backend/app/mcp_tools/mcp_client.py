"""
MCP 서버에 연결해 제공되는 도구를 조회하고 호출하는 코드.
"""
import os
from contextlib import AsyncExitStack
from typing import Any, Optional

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client

load_dotenv()


class MCPGatewayClient:
    def __init__(self):
        self._session: Optional[ClientSession] = None
        self._stack: Optional[AsyncExitStack] = None
        self._tool_names: set[str] = set()

    @property
    def connected(self) -> bool:
        return self._session is not None

    async def connect(self) -> None:
        transport = os.getenv("MCP_TRANSPORT")
        if not transport:
            return  # 실제 서버 미설정 -> mock만 사용

        self._stack = AsyncExitStack()

        if transport == "stdio":
            command = os.getenv("MCP_SERVER_COMMAND")
            args = os.getenv("MCP_SERVER_ARGS", "").split()
            params = StdioServerParameters(command=command, args=args, env=dict(os.environ))
            read, write = await self._stack.enter_async_context(stdio_client(params))

        elif transport == "http":
            url = os.getenv("MCP_SERVER_URL")
            read, write, _ = await self._stack.enter_async_context(streamable_http_client(url))

        else:
            raise ValueError(f"알 수 없는 MCP_TRANSPORT: {transport}")

        session = await self._stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self._session = session

        tools = await session.list_tools()
        self._tool_names = {t.name for t in tools.tools}

    async def disconnect(self) -> None:
        if self._stack:
            await self._stack.aclose()
        self._session = None
        self._tool_names = set()

    def has_tool(self, name: str) -> bool:
        return name in self._tool_names

    async def list_tools(self) -> list[dict]:
        if not self._session:
            return []
        tools = await self._session.list_tools()
        return [
            {"name": t.name, "description": t.description, "input_schema": t.input_schema}
            for t in tools.tools
        ]

    async def call_tool(self, name: str, arguments: dict) -> Any:
        result = await self._session.call_tool(name, arguments)
        if result.is_error:
            return {"error": str(result.content)}
        parts = [c.text for c in result.content if getattr(c, "type", None) == "text"]
        return {"text": "\n".join(parts)} if parts else {"content": result.content}


mcp_client = MCPGatewayClient()
