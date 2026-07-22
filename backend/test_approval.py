"""
관리자 승인 흐름 테스트.

실행: python test_approval.py
"""
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.database import engine
from app.models import Approval


def run():
    with TestClient(app) as client:
        def call(**kw):
            return client.post("/v1/tool_call", json=kw).json()

        print("=" * 60)

        # --- 승인 대기 만들기: 진료기록 3회 조회 -> 3번째가 60점(승인 구간) ---
        for pid in ("P1001", "P1002"):
            call(session_id="A1", user_request="환자 상태 확인",
                 tool="get_medical_record", arguments={"patient_id": pid}, user_role="doctor")
        r = call(session_id="A1", user_request="환자 상태 확인",
                 tool="get_medical_record", arguments={"patient_id": "P1001"}, user_role="doctor")
        print(f"[요청] 3번째 조회 -> decision={r['decision']} ({r['risk_score']}점), approval_id={r['approval_id']}")
        ap_id = r["approval_id"]
        assert r["decision"] == "approve" and ap_id is not None

        # --- 관리자: 대기 목록 확인 ---
        pending = client.get("/approvals", params={"status": "pending"}).json()
        print(f"[관리자] 대기 목록 {len(pending)}건, 첫 건 사유={pending[0]['reasons']}")

        # --- 에이전트: 폴링 (아직 대기) ---
        s = client.get(f"/approvals/{ap_id}").json()
        print(f"[폴링] 상태={s['status']} (아직 결정 전, result={s['result']})")

        # --- 관리자: 승인 -> 이때 도구 실행됨 ---
        d = client.post(f"/approvals/{ap_id}/decide", json={"decision": "approve", "admin_id": "admin01"}).json()
        print(f"[승인] 상태={d['status']}, 결정자={d['decided_by']}")
        print(f"       실행 결과={d['result']}")
        assert d["status"] == "approved" and d["result"] is not None

        # --- 에이전트: 다시 폴링 -> 이제 결과 받음 ---
        s2 = client.get(f"/approvals/{ap_id}").json()
        print(f"[폴링] 상태={s2['status']} -> result 받음: {s2['result']}")

        # --- 중복 결정 방지 ---
        again = client.post(f"/approvals/{ap_id}/decide", json={"decision": "approve"})
        print(f"[중복] 이미 처리된 건 재결정 -> HTTP {again.status_code} ({again.json()['detail']})")
        assert again.status_code == 409

        # --- 거부 시나리오 ---
        for pid in ("P1001", "P1002"):
            call(session_id="A2", user_request="환자 상태 확인",
                 tool="get_medical_record", arguments={"patient_id": pid}, user_role="doctor")
        r2 = call(session_id="A2", user_request="환자 상태 확인",
                  tool="get_medical_record", arguments={"patient_id": "P1001"}, user_role="doctor")
        d2 = client.post(f"/approvals/{r2['approval_id']}/decide", json={"decision": "reject"}).json()
        print(f"[거부] 상태={d2['status']}, result={d2['result']}")
        assert d2["status"] == "rejected"

        # --- 시간 초과(자동 거부) 시나리오 ---
        for pid in ("P1001", "P1002"):
            call(session_id="A3", user_request="환자 상태 확인",
                 tool="get_medical_record", arguments={"patient_id": pid}, user_role="doctor")
        r3 = call(session_id="A3", user_request="환자 상태 확인",
                  tool="get_medical_record", arguments={"patient_id": "P1001"}, user_role="doctor")
        with Session(engine) as db:
            ap = db.get(Approval, r3["approval_id"])
            ap.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
            db.add(ap); db.commit()
        expired = client.get(f"/approvals/{r3['approval_id']}").json()
        print(f"[만료] 제한시간 지난 대기건 조회 -> 상태={expired['status']}")
        assert expired["status"] == "expired"

        print("=" * 60)
        print("완료: 승인 / 거부 / 중복방지 / 자동만료 전부 정상 작동.")


if __name__ == "__main__":
    run()