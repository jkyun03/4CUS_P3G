"""
리포트 내보내기 API. ('리포트' 기능 2단계 - CSV)

events 테이블을 CSV 파일로 만들어 다운로드시킨다.
- 엑셀에서 한글이 깨지지 않도록 맨 앞에 BOM을 붙인다.
"""
import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.database import get_session
from app.models import Event

router = APIRouter()


@router.get("/reports/events.csv")
def export_events_csv(db: Session = Depends(get_session)):
    events = db.exec(select(Event).order_by(Event.id)).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["이벤트ID", "시각", "세션", "도구", "위험점수", "판정", "마스킹", "탐지사유"]
    )
    for e in events:
        writer.writerow([
            e.id,
            e.created_at.isoformat() if e.created_at else "",
            e.session_id,
            e.tool_name,
            e.risk_score,
            e.decision,
            "예" if e.masked else "아니오",
            " | ".join(e.reasons or []),
        ])

    csv_text = "\ufeff" + buf.getvalue()  # BOM + 내용 (엑셀 한글 깨짐 방지)
    headers = {"Content-Disposition": "attachment; filename=events_report.csv"}
    return StreamingResponse(iter([csv_text]), media_type="text/csv", headers=headers)