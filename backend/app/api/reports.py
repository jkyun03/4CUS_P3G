import csv
import io
from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

from app.database import get_session
from app.models import Event

router = APIRouter()

pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
KOR_FONT = "HYSMyeongJo-Medium"


@router.get("/reports/events.csv")
def export_events_csv(db: Session = Depends(get_session)):
    events = db.exec(select(Event).order_by(Event.id)).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["이벤트ID", "시각", "세션", "도구", "위험점수", "판정", "마스킹", "탐지사유"])
    for e in events:
        writer.writerow([
            e.id,
            e.created_at.isoformat() if e.created_at else "",
            e.session_id, e.tool_name, e.risk_score, e.decision,
            "예" if e.masked else "아니오",
            " | ".join(e.reasons or []),
        ])
    csv_text = "\ufeff" + buf.getvalue()
    headers = {"Content-Disposition": "attachment; filename=events_report.csv"}
    return StreamingResponse(iter([csv_text]), media_type="text/csv", headers=headers)


@router.get("/reports/events.pdf")
def export_events_pdf(db: Session = Depends(get_session)):
    events = db.exec(select(Event).order_by(Event.id)).all()
    by_decision = Counter(e.decision for e in events)
    masked_cnt = sum(1 for e in events if e.masked)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    base = getSampleStyleSheet()
    title_style = ParagraphStyle("t", parent=base["Title"], fontName=KOR_FONT)
    normal = ParagraphStyle("n", parent=base["Normal"], fontName=KOR_FONT, fontSize=10, leading=16)

    story = []
    story.append(Paragraph("IDEA Gateway 보안 리포트", title_style))
    story.append(Paragraph("생성 시각: " + datetime.now().strftime("%Y-%m-%d %H:%M"), normal))
    story.append(Paragraph(
        f"총 이벤트 {len(events)}건  ·  차단 {by_decision.get('block', 0)}건  ·  "
        f"마스킹 {masked_cnt}건  ·  승인필요 {by_decision.get('approve', 0)}건",
        normal,
    ))
    story.append(Spacer(1, 8 * mm))

    data = [["ID", "시각", "도구", "점수", "판정", "마스킹"]]
    for e in events:
        data.append([
            str(e.id),
            e.created_at.strftime("%m-%d %H:%M") if e.created_at else "",
            e.tool_name,
            str(e.risk_score),
            e.decision,
            "예" if e.masked else "-",
        ])
    table = Table(data, colWidths=[14 * mm, 28 * mm, 48 * mm, 16 * mm, 24 * mm, 18 * mm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), KOR_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#202020")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d6dee6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)

    doc.build(story)
    buf.seek(0)
    headers = {"Content-Disposition": "attachment; filename=security_report.pdf"}
    return StreamingResponse(buf, media_type="application/pdf", headers=headers)