"""
툴 포이즈닝(Tool Poisoning) 탐지기.

MCP 도구는 이름/설명(description)이 그대로 LLM에게 노출된다. 공격자는 이 설명 안에
숨겨진 지시문을 심어 에이전트를 조종하거나(Tool Poisoning), 사용자가 한 번 승인한
뒤에 몰래 설명/정의를 바꿔치기(rug-pull)할 수 있다.

변조 탐지는 해시 완전일치가 아니라 '의미 유사도'로 판단한다. 오탈자 수정처럼 사소한
변경까지 전부 차단해버리면 오탐이 너무 많아지기 때문 — 최초 등록 시점 설명(baseline)과
지금 설명이 여전히 의미적으로 비슷하면 그냥 넘어가고(baseline만 갱신), 의미 자체가
달라졌을 때만 rug-pull로 본다.

이 파일도 core/ 관례대로 FastAPI/DB에 의존하지 않는 순수 파이썬이다. 유사도 계산은
외부 API 호출 없이 로컬에서 즉시 계산된다(비용 없음).
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core import prompt_injection

# 이 값보다 낮으면 '의미가 실질적으로 바뀜' -> 변조 의심.
# 오탈자 수정 같은 사소한 변화는 대체로 이 값 이상으로 유사하게 나온다.
SIMILARITY_THRESHOLD = 0.80


def scan_description(description: str) -> list[str]:
    """도구 설명 안에 숨겨진 지시문(프롬프트 인젝션과 동일 패턴)이 있는지 확인한다."""
    return prompt_injection.scan(description)


def semantic_similarity(text_a: str, text_b: str) -> float:
    """두 설명 문자열의 의미적 유사도(0~1). 문자 n-gram TF-IDF 코사인 유사도로 근사한다."""
    if not text_a and not text_b:
        return 1.0
    if not text_a or not text_b:
        return 0.0
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
    vectors = vectorizer.fit_transform([text_a, text_b])
    return float(cosine_similarity(vectors[0], vectors[1])[0][0])


def check_tampering(name: str, current_description: str, baseline_description) -> tuple:
    """
    현재 설명을 최초 등록 시점(baseline) 설명과 비교한다.
    반환: (변조_이유 또는 None, 새로 저장할 baseline_description)
      - baseline이 없으면(최초 확인) 지금 값을 기준으로 삼는다 -> 변조 아님.
      - 완전히 같으면 -> 변조 아님.
      - 의미적으로 여전히 비슷하면(오탈자 수정 등) -> 변조 아님, baseline을 지금 값으로 갱신.
      - 의미가 실질적으로 달라졌으면 -> 변조 의심, baseline은 그대로 유지(관리자 확인 전까지 계속 차단).
    """
    if baseline_description is None:
        return None, current_description
    if baseline_description == current_description:
        return None, baseline_description

    similarity = semantic_similarity(baseline_description, current_description)
    if similarity >= SIMILARITY_THRESHOLD:
        return None, current_description  # 사소한 수정 -> 새 설명을 새 baseline으로 채택

    return (f"도구 정의 변조 감지(rug-pull 의심): '{name}'의 설명이 최초 등록 이후 "
            f"의미적으로 달라짐(유사도 {similarity:.2f})"), baseline_description
