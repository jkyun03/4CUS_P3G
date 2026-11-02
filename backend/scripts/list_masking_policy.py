"""
직군별 필드 마스킹 정책을 표로 출력한다.
실행: backend 폴더에서 python -m scripts.list_masking_policy
"""
from app.core.masking import FIELD_POLICY, DEFAULT_POLICY

FIELDS = ["name", "rrn", "phone", "diagnosis", "content", "next_appointment", "patient_id"]

print(f"{'role':<20} " + " ".join(f"{f:<18}" for f in FIELDS))
print("-" * 150)
for role, policy in FIELD_POLICY.items():
    row = " ".join(f"{policy.get(f, '-'):<18}" for f in FIELDS)
    print(f"{role:<20} {row}")

print("-" * 150)
row = " ".join(f"{DEFAULT_POLICY.get(f, '-'):<18}" for f in FIELDS)
print(f"{'(미등록 role 기본값)':<20} {row}")
