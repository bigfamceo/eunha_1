from fpdf import FPDF
from fpdf.enums import XPos, YPos
import student_data as sd
import tempfile

FONT_PATH = "NanumGothic.ttf"


def get_monthly_stats(name, year, month):
    """특정 학생의 특정 월 데이터를 모아서 통계 계산"""
    year_month = f"{year}-{month:02d}"

    all_records = sd.get_study_records(name)
    records = [r for r in all_records if str(r["날짜"]).startswith(year_month)]

    all_reflections = sd.get_student_reflections(name)
    reflections = [r for r in all_reflections if str(r["작성일자"]).startswith(year_month)]

    all_feedbacks = sd.get_teacher_feedback(name)
    feedbacks = [f for f in all_feedbacks if str(f["작성일자"]).startswith(year_month)]

    total_days = len(records)
    total_read = sum(int(r["읽은횟수"]) for r in records) if records else 0

    # 목표시간 달성 여부(O/X)를 하루 단위로 판단
    achieved_days = sum(
        1 for r in records if int(r["리딩_성취시간"]) >= int(r["리딩_목표시간"])
    ) if records else 0
    not_achieved_days = total_days - achieved_days

    dictation_rate = round(sum(1 for r in records if r["딕테이션"] == "O") / total_days * 100, 1) if total_days > 0 else 0
    vocab_rate = round(sum(1 for r in records if r["어휘"] == "O") / total_days * 100, 1) if total_days > 0 else 0

    stats = {
        "총_학습일수": total_days,
        "총_읽은횟수": total_read,
        "목표달성_O": achieved_days,
        "목표달성_X": not_achieved_days,
        "딕테이션_성공률": dictation_rate,
        "어휘_성공률": vocab_rate,
    }

    return records, reflections, feedbacks, stats


def generate_pdf(name, year, month):
    """월말 보고서 PDF 생성 후 바이트로 반환"""
    records, reflections, feedbacks, stats = get_monthly_stats(name, year, month)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font("Nanum", "", FONT_PATH)
    pdf.set_font("Nanum", "", 18)
    pdf.cell(0, 12, f"{name} 학생 {year}년 {month}월 학습 리포트", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    pdf.set_font("Nanum", "", 13)
    pdf.cell(0, 10, "학습 요약", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Nanum", "", 11)
    pdf.cell(0, 8, f"총 학습일수: {stats['총_학습일수']}일", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"총 읽은 횟수: {stats['총_읽은횟수']}회", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"목표 달성: O {stats['목표달성_O']}일 / X {stats['목표달성_X']}일", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"딕테이션 성공률: {stats['딕테이션_성공률']}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"어휘 성공률: {stats['어휘_성공률']}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    pdf.set_font("Nanum", "", 13)
    pdf.cell(0, 10, "교사 피드백", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Nanum", "", 11)
    if feedbacks:
        for f in feedbacks:
            pdf.multi_cell(0, 7, f"[{f['작성일자']} · {f['주차']}] {f['교사_피드백']}",
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT, wrapmode="CHAR")
            pdf.ln(1)
    else:
        pdf.cell(0, 8, "작성된 피드백이 없습니다.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    pdf.set_font("Nanum", "", 13)
    pdf.cell(0, 10, "학생 소감", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Nanum", "", 11)
    if reflections:
        for r in reflections:
            pdf.multi_cell(0, 7, f"[{r['작성일자']}]", new_x=XPos.LMARGIN, new_y=YPos.NEXT, wrapmode="CHAR")
            pdf.multi_cell(0, 7, f"느낀점: {r['학습_느낀점']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, wrapmode="CHAR")
            pdf.multi_cell(0, 7, f"감사한 점: {r['감사한_점']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, wrapmode="CHAR")
            pdf.multi_cell(0, 7, f"역경 극복: {r['역경_극복한_점']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, wrapmode="CHAR")
            pdf.multi_cell(0, 7, f"칭찬받은 점: {r['칭찬_받은_점']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, wrapmode="CHAR")
            pdf.ln(2)
    else:
        pdf.cell(0, 8, "작성된 소감이 없습니다.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp_path = tmp.name

    with open(tmp_path, "rb") as f:
        pdf_bytes = f.read()

    return pdf_bytes