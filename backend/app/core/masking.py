"""
민감정보 마스킹 유틸리티.

지금은 '블랙리스트' 방식이다: 아래에 정한 민감한 키/패턴을 발견하면 가린다.
=> 담당자(서희)가 나중에 '화이트리스트' 방식(허용된 항목만 남기고 전부 가림)으로
   확장할 예정. 이 파일이 그 출발점이다.
"""
import re

# 문자열 안에서 찾아낼 패턴들
RRN = re.compile(r"\d{6}-\d{7}")                       # 주민등록번호
PHONE = re.compile(r"01[016789]-?\d{3,4}-?\d{4}")      # 휴대폰 번호
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")        # 이메일

# 이 키(항목)에 담긴 값은 통째로 가린다.
SENSITIVE_KEYS = {"rrn", "phone", "diagnosis", "content", "medical_record"}


def _mask_value(key: str, value):
    """값 하나를 규칙에 따라 가린다."""
    if not isinstance(value, str):
        return value

    # 이름은 첫 글자만 남기고 가린다: 김민수 -> 김**
    if key == "name" and len(value) >= 2:
        return value[0] + "*" * (len(value) - 1)

    # 민감 키는 통째로 비식별
    if key in SENSITIVE_KEYS:
        return "[비식별]"

    # 그 외 문자열은 패턴이 보이면 그 부분만 가린다
    value = RRN.sub(lambda m: m.group()[:7] + "*******", value)
    value = PHONE.sub("010-****-****", value)
    value = EMAIL.sub(lambda m: m.group()[0] + "***@***", value)
    return value


def mask_data(data):
    """dict / list 를 재귀적으로 훑어 민감정보를 가린 새 데이터를 돌려준다."""
    if isinstance(data, dict):
        return {
            k: (mask_data(v) if isinstance(v, (dict, list)) else _mask_value(k, v))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [mask_data(x) for x in data]
    return data
