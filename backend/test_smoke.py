"""
스모크 테스트: python test_smoke.py
"""
from fastapi.testclient import TestClient
from app.main import app


def run():
    with TestClient(app) as client:
        def call(session_id, tool, arguments, role, user_id="", request="테스트 요청"):
            body = {"session_id": session_id, "user_request": request, "tool": tool,
                     "arguments": arguments, "user_role": role, "user_id": user_id}
            return client.post("/v1/tool_call", json=body).json()

        print("=" * 70)

        r = call("S1", "get_medical_record", {"patient_id": "P1001"}, "doctor", "doctor_kim")
        print("[의사-담당환자] ", r["result"])
        assert r["result"]["diagnosis"] == "고혈압"

        r = call("S2", "get_medical_record", {"patient_id": "P1002"}, "doctor", "doctor_kim")
        print("[의사-비담당환자]", r["result"])
        assert r["result"]["diagnosis"] == "[비식별]"

        r = call("S3", "get_medical_record", {"patient_id": "P1001"}, "nurse", "nurse_lee")
        print("[간호사-담당환자]", r["result"])
        assert r["result"]["diagnosis"] == "고혈압"

        r = call("S4", "get_medical_record", {"patient_id": "P1002"}, "nurse", "nurse_lee")
        print("[간호사-비담당환자]", r["result"])
        assert r["result"]["diagnosis"] == "[비식별]"

        r = call("S5", "get_medical_record", {"patient_id": "P1001"}, "pharmacist")
        print("[약사]", r["result"])
        assert r["result"]["diagnosis"] == "고혈압"
        assert r["result"]["content"] == "[비식별]"

        r = call("S5b", "get_appointment", {"patient_id": "P1001"}, "pharmacist")
        print("[약사-예약조회 시도]", r["result"])
        assert r["result"]["next_appointment"] == "[접근불가]"

        r = call("S6", "get_medical_record", {"patient_id": "P1001"}, "security_officer")
        print("[보안담당자]", r["result"])
        assert r["result"]["patient_id"] == "P1***"

        r = call("S7", "get_medical_record", {"patient_id": "P1001"}, "guest")
        print("[미등록 role]", r["result"])
        assert r["result"]["diagnosis"] == "[비식별]"

        r = call("S8", "send_email", {"to": "x@y.com", "body": "..."}, "intern")
        print("[실습생-메일발송 시도]", r["decision"], r["reasons"])
        assert r["decision"] == "block"

        print("=" * 70)
        print("전부 통과: 담당 환자 여부 + 직군별 마스킹 등급 정상 작동.")


if __name__ == "__main__":
    run()
    