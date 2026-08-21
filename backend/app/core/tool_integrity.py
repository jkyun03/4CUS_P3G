from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core import prompt_injection

SIMILARITY_THRESHOLD = 0.80


def scan_description(description: str) -> list[str]:
    return prompt_injection.scan(description)


def semantic_similarity(text_a: str, text_b: str) -> float:
    if not text_a and not text_b:
        return 1.0
    if not text_a or not text_b:
        return 0.0
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
    vectors = vectorizer.fit_transform([text_a, text_b])
    return float(cosine_similarity(vectors[0], vectors[1])[0][0])


def check_tampering(name: str, current_description: str, baseline_description) -> tuple:
    if baseline_description is None:
        return None, current_description
    if baseline_description == current_description:
        return None, baseline_description

    similarity = semantic_similarity(baseline_description, current_description)
    if similarity >= SIMILARITY_THRESHOLD:
        return None, current_description

    return (f"도구 정의 변조 감지(rug-pull 의심): '{name}'의 설명이 최초 등록 이후 "
            f"의미적으로 달라짐(유사도 {similarity:.2f})"), baseline_description
