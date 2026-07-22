"""
스모크 테스트: 서버를 띄우지 않고도 핵심 시나리오를 빠르게 확인한다.

실행: (backend 폴더에서)
    python test_smoke.py

※ 'with TestClient(app) as client' 형태로 써야 서버 시작 이벤트
  (테이블 생성 + 초기 도구 삽입)가 실행된다.
"""
from fastapi.testclient import TestClient
from app.main import app


def run():
    with TestClient(app) as client:   # <- 이 with 블록이 startup 을 실행시킨다
        def call(**kw):
            return client.post("/v1/tool_call", json=kw).json()

        print("=" * 60)

        # 1) 정상 흐름: 예약 조회 (위험 없음 -> 허용)
        r = call(session_id="S1", user_request="김민수 환자 예약 알려줘",
                 tool="search_patient", arguments={"name": "김민수"}, user_role="doctor")
        print(f"[정상] search_patient  -> {r['decision']} ({r['risk_score']}점)")

        r = call(session_id="S1", user_request="김민수 환자 예약 알려줘",
                 tool="get_appointment", arguments={"patient_id": "P1001"}, user_role="doctor")
        print(f"[정상] get_appointment -> {r['decision']} ({r['risk_score']}점) result={r['result']}")

        # 2) 마스킹: 진료기록 조회는 기본적으로 가려서 반환
        r = call(session_id="S2", user_request="김민수 진료기록 보여줘",
                 tool="get_medical_record", arguments={"patient_id": "P1001"}, user_role="doctor")
        print(f"[마스킹] get_medical_record -> {r['decision']} (masked={r['masked']})")
        print(f"         결과: {r['result']}")

        # 3) 차단: '예약 문의'인데 진료기록 조회 후 외부 메일 전송
        call(session_id="S3", user_request="김민수 예약 알려줘",
             tool="get_medical_record", arguments={"patient_id": "P1001"}, user_role="admin")
        r = call(session_id="S3", user_request="김민수 예약 알려줘",
                 tool="send_email", arguments={"to": "attacker@gmail.com", "body": "..."}, user_role="admin")
        print(f"[차단] send_email(외부) -> {r['decision']} ({r['risk_score']}점)")
        print(f"       사유: {r['reasons']}")

        # 4) 비활성화된 도구 (export_csv 는 enabled=False)
        r = call(session_id="S4", user_request="데이터 내보내줘",
                 tool="export_csv", arguments={}, user_role="admin")
        print(f"[권한] export_csv -> {r['decision']}  사유: {r['reasons']}")

        # 5) 권한 없음: nurse 가 진료기록 조회 (허용 역할: doctor, admin)
        r = call(session_id="S5", user_request="기록 보여줘",
                 tool="get_medical_record", arguments={"patient_id": "P1001"}, user_role="nurse")
        print(f"[권한] nurse 진료기록 -> {r['decision']}  사유: {r['reasons']}")

        print("=" * 60)
        print("완료: 위 결과가 기대대로면 백엔드 뼈대가 정상 작동하는 것.")


if __name__ == "__main__":
    run()
