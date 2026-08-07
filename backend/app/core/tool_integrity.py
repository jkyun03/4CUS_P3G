"""
툴 포이즈닝(Tool Poisoning) 탐지기.

MCP 도구는 이름/설명(description)이 그대로 LLM에게 노출된다. 공격자는 이 설명 안에
숨겨진 지시문을 심어 에이전트를 조종하거나(Tool Poisoning), 사용자가 한 번 승인한
뒤에 몰래 설명/정의를 바꿔치기(rug-pull)할 수 있다.

이 파일도 core/ 관례대로 FastAPI/DB에 의존하지 않는 순수 파이썬이다.
"""
import hashlib

from app.core import prompt_injection


def scan_description(description: str) -> list[str]:
    """도구 설명 안에 숨겨진 지시문(프롬프트 인젝션과 동일 패턴)이 있는지 확인한다."""
    return prompt_injection.scan(description)


def compute_signature(name: str, description: str) -> str:
    """도구 정의(이름+설명)의 지문. 이후 이 값이 바뀌면 '몰래 변조'로 본다."""
    raw = f"{name}::{description}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def check_tampering(name: str, description: str, stored_hash) -> tuple:
    """
    등록된 해시와 현재 설명의 해시를 비교한다.
    반환: (변조_이유 또는 None, 현재_해시)
      - stored_hash 가 없으면(최초 확인) 지금 값을 기준(baseline)으로 삼는다 -> 변조 아님.
      - 있는데 다르면 -> 최초 등록 이후 몰래 바뀐 것 -> 변조 의심.
    """
    current_hash = compute_signature(name, description)
    if stored_hash is None:
        return None, current_hash
    if stored_hash != current_hash:
        return (f"도구 정의 변조 감지(rug-pull 의심): '{name}'의 설명이 "
                f"최초 등록 이후 변경됨"), current_hash
    return None, current_hash
