"""
환자별 담당의/담당간호사/주민번호/전화번호/진단명/소견내용을 표로 출력한다.
실행: python list_patients.py
"""
from app.mcp_tools.registry import PATIENTS, RECORDS

print(f"{'patient_id':<10} {'이름':<8} {'주민번호':<16} {'전화번호':<15} "
      f"{'담당의':<14} {'담당간호사':<14} {'진단명':<18} {'소견내용'}")
print("-" * 140)

for pid, p in PATIENTS.items():
    diagnosis = RECORDS[pid]["diagnosis"]
    content = RECORDS[pid]["content"]
    print(f"{pid:<10} {p['name']:<8} {p['rrn']:<16} {p['phone']:<15} "
          f"{p['attending_doctor']:<14} {p['attending_nurse']:<14} {diagnosis:<18} {content}")