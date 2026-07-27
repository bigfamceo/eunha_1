import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import re
import os
import uuid

# ===== 초기 설정 =====
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
JSON_KEY_PATH = "json key/eunha-1.json"
SHEET_NAME = "eunha1"

POINT_PER_DAY = 100  # 학습일지 / 바이탈체크 하루 1회 이상 기록 시 포인트


def get_spreadsheet():
    """구글 스프레드시트 연결 객체 반환
    - Streamlit Cloud(배포 환경)에서는 st.secrets 사용
    - 로컬(내 컴퓨터)에서는 JSON 키 파일 사용
    """
    try:
        import streamlit as st
        # secrets.toml에 [gcp_service_account] 항목이 있으면 그걸 사용
        if "gcp_service_account" in st.secrets:
            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes=SCOPES
            )
            client = gspread.authorize(credentials)
            return client.open(SHEET_NAME)
    except Exception:
        # streamlit이 없거나 secrets 접근 실패 시 로컬 방식으로 넘어감
        pass

    # 로컬 환경: JSON 키 파일 사용
    credentials = Credentials.from_service_account_file(JSON_KEY_PATH, scopes=SCOPES)
    client = gspread.authorize(credentials)
    return client.open(SHEET_NAME)


def get_or_create_worksheet(sh, name, headers):
    """시트가 없으면 새로 만들고 헤더를 넣어줌"""
    try:
        ws = sh.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=name, rows=1000, cols=len(headers))
        ws.append_row(headers)
    return ws


# ===== 1. 로그인 =====
def login(name, password):
    """이름 + 비밀번호로 학생 확인. 성공하면 학생 정보 dict, 실패하면 None 반환"""
    sh = get_spreadsheet()
    ws = sh.worksheet("학생_명부")
    records = ws.get_all_records(expected_headers=["학생ID", "이름", "학년", "비밀번호"])

    for row in records:
        if str(row["이름"]) == name and str(row["비밀번호"]) == password:
            return row
    return None


def get_all_student_names():
    """전체 학생 명단 (랭킹판에 0점 학생도 표시하기 위함)"""
    sh = get_spreadsheet()
    ws = sh.worksheet("학생_명부")
    records = ws.get_all_records(expected_headers=["학생ID", "이름", "학년", "비밀번호"])
    return [r["이름"] for r in records if r.get("이름")]


# ===== 2. 학습_기록 추가 =====
def add_study_record(name, target_time, achieved_time, read_count, dictation, vocab):
    """학생이 오늘 학습한 내용을 기록"""
    sh = get_spreadsheet()
    ws = sh.worksheet("학습_기록")
    today = datetime.now().strftime("%Y-%m-%d")
    ws.append_row([today, name, target_time, achieved_time, read_count, dictation, vocab])


# ===== 3. 학습_기록 조회 =====
def get_study_records(name, start_date=None, end_date=None):
    """특정 학생의 학습 기록 조회 (기간 필터 옵션)"""
    sh = get_spreadsheet()
    ws = sh.worksheet("학습_기록")
    records = ws.get_all_records(expected_headers=[
        "날짜", "학생이름", "리딩_목표시간", "리딩_성취시간", "읽은횟수", "딕테이션", "어휘"
    ])

    result = [row for row in records if str(row["학생이름"]) == name]

    if start_date:
        result = [row for row in result if str(row["날짜"]) >= start_date]
    if end_date:
        result = [row for row in result if str(row["날짜"]) <= end_date]

    return result


# ===== 4. 교사_피드백 조회/추가 =====
def get_teacher_feedback(name, start_date=None, end_date=None):
    """특정 학생에 대한 교사 피드백 조회"""
    sh = get_spreadsheet()
    ws = sh.worksheet("교사_피드백")
    records = ws.get_all_records(expected_headers=["작성일자", "학생이름", "주차", "교사_피드백"])

    result = [row for row in records if str(row["학생이름"]) == name]

    if start_date:
        result = [row for row in result if str(row["작성일자"]) >= start_date]
    if end_date:
        result = [row for row in result if str(row["작성일자"]) <= end_date]

    return result


def add_teacher_feedback(name, week, content, date=None):
    """교사가 주간 피드백 작성"""
    sh = get_spreadsheet()
    ws = sh.worksheet("교사_피드백")
    date_str = date.strftime("%Y-%m-%d") if date else datetime.now().strftime("%Y-%m-%d")
    ws.append_row([date_str, name, week, content])


# ===== 5. 바이탈체크(학생 소감) 추가/조회 (긍정심리학 6항목, 비공개) =====
def add_student_reflection(name, gratitude, love, praise, overcome, curiosity, challenge):
    """학생이 직접 작성하는 소감 (긍정심리학 6항목).
    '감사한 일' 항목은 감사나눔 공개 게시판에도 자동으로 함께 올라감."""
    sh = get_spreadsheet()
    ws = sh.worksheet("바이탈체크")
    today = datetime.now().strftime("%Y-%m-%d")
    ws.append_row([today, name, gratitude, love, praise, overcome, curiosity, challenge])

    # 감사한 일이 있으면 공개 게시판에도 자동 공유
    if gratitude and gratitude.strip():
        add_gratitude_post(name, gratitude.strip())


def get_student_reflections(name, start_date=None, end_date=None):
    """특정 학생의 소감 기록 조회"""
    sh = get_spreadsheet()
    ws = sh.worksheet("바이탈체크")
    records = ws.get_all_records(expected_headers=[
        "작성일자", "학생이름", "감사한_일", "사랑을_경험한_일",
        "남을_칭찬하거나_격려한_일", "역경을_극복한_일", "호기심_궁금했던_점", "도전해_본_일"
    ])

    result = [row for row in records if str(row["학생이름"]) == name]

    if start_date:
        result = [row for row in result if str(row["작성일자"]) >= start_date]
    if end_date:
        result = [row for row in result if str(row["작성일자"]) <= end_date]

    return result


# ===== 6. 감사나눔 공개 게시판 + 좋아요 =====
def add_gratitude_post(name, content):
    """감사한 일을 감사나눔 공개 게시판에 게시 (바이탈체크 저장 시 자동 호출됨)"""
    if not content or not content.strip():
        return
    sh = get_spreadsheet()
    ws = get_or_create_worksheet(sh, "감사나눔", ["ID", "날짜", "이름", "내용", "좋아요수"])
    post_id = str(uuid.uuid4())
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    ws.append_row([post_id, now_str, name, content, 0])


def get_gratitude_posts(viewer_name=None):
    """감사나눔 게시글 전체 조회 (최신순). viewer_name을 넣으면 내가 좋아요 눌렀는지 여부도 함께 반환"""
    sh = get_spreadsheet()
    ws = get_or_create_worksheet(sh, "감사나눔", ["ID", "날짜", "이름", "내용", "좋아요수"])
    like_ws = get_or_create_worksheet(sh, "좋아요기록", ["날짜", "게시글ID", "누른사람"])

    posts = ws.get_all_records(expected_headers=["ID", "날짜", "이름", "내용", "좋아요수"])
    likes = like_ws.get_all_records(expected_headers=["날짜", "게시글ID", "누른사람"])
    liked_ids = {l["게시글ID"] for l in likes if l["누른사람"] == viewer_name} if viewer_name else set()

    result = []
    for p in posts:
        if not p.get("ID"):
            continue
        result.append({
            "id": p["ID"],
            "date": p["날짜"],
            "name": p["이름"],
            "content": p["내용"],
            "likes": p["좋아요수"] or 0,
            "liked_by_me": p["ID"] in liked_ids
        })

    result.sort(key=lambda x: x["date"], reverse=True)
    return result


def add_like(post_id, liker_name):
    """감사나눔 게시글에 좋아요 추가 (한 사람당 한 게시글에 1번만, 랭킹과는 무관한 순수 응원 기능)"""
    if not post_id or not liker_name:
        return False

    sh = get_spreadsheet()
    like_ws = get_or_create_worksheet(sh, "좋아요기록", ["날짜", "게시글ID", "누른사람"])
    likes = like_ws.get_all_records(expected_headers=["날짜", "게시글ID", "누른사람"])

    for l in likes:
        if l["게시글ID"] == post_id and l["누른사람"] == liker_name:
            return False  # 이미 좋아요 누름

    like_ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), post_id, liker_name])

    post_ws = sh.worksheet("감사나눔")
    cell = post_ws.find(post_id)
    if cell:
        current = post_ws.cell(cell.row, 5).value  # E열 = 좋아요수
        current = int(current) if current else 0
        post_ws.update_cell(cell.row, 5, current + 1)

    return True


# ===== 7. 랭킹 (성실왕 / 감사왕) =====
def get_period_range(period):
    """'week' / 'month' / 'all' 에 따른 시작~끝 날짜 범위"""
    now = datetime.now()
    if period == "week":
        monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        return monday, now
    elif period == "month":
        first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return first, now
    return None, None


def get_day_count_map(sheet_name, date_field, name_field, period):
    """시트에서 학생별 '기록이 있었던 날짜 수' 계산 (이름 -> 일수)"""
    sh = get_spreadsheet()
    ws = sh.worksheet(sheet_name)
    records = ws.get_all_records()

    start, end = get_period_range(period)
    day_map = {}

    for r in records:
        date_str = str(r.get(date_field, "")).strip()
        name = r.get(name_field)
        if not date_str or not name:
            continue
        try:
            d = datetime.strptime(date_str[:10], "%Y-%m-%d")
        except ValueError:
            continue
        if start and d < start:
            continue
        if end and d > end:
            continue
        day_map.setdefault(name, set()).add(date_str[:10])

    return {name: len(dates) for name, dates in day_map.items()}


def get_study_ranking(period):
    """성실왕 랭킹: 학습일지 기록일수 x 100점"""
    names = get_all_student_names()
    counts = get_day_count_map("학습_기록", "날짜", "학생이름", period)
    result = [{"name": n, "points": counts.get(n, 0) * POINT_PER_DAY} for n in names]
    result.sort(key=lambda x: -x["points"])
    return result


def get_vital_ranking(period):
    """감사왕 랭킹: 바이탈체크 기록일수 x 100점"""
    names = get_all_student_names()
    counts = get_day_count_map("바이탈체크", "작성일자", "학생이름", period)
    result = [{"name": n, "points": counts.get(n, 0) * POINT_PER_DAY} for n in names]
    result.sort(key=lambda x: -x["points"])
    return result


def get_my_total_points(name):
    """내 누적 총점 (기간 무관, 전체 누적)"""
    study = get_day_count_map("학습_기록", "날짜", "학생이름", "all")
    vital = get_day_count_map("바이탈체크", "작성일자", "학생이름", "all")
    s = study.get(name, 0) * POINT_PER_DAY
    v = vital.get(name, 0) * POINT_PER_DAY
    return {"study": s, "vital": v, "total": s + v}


# ===== 8. 구글폼 응답 동기화 =====
def parse_timestamp_date(timestamp_str):
    """구글폼 타임스탬프 문자열에서 날짜(YYYY-MM-DD)만 추출"""
    match = re.match(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})", timestamp_str.strip())
    if match:
        y, m, d = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"
    return datetime.now().strftime("%Y-%m-%d")


def sync_form_responses():
    """숙제_응답 탭의 새 구글폼 응답을 학습_기록 + 바이탈체크로 동기화. 새로 옮긴 개수 반환"""
    sh = get_spreadsheet()
    ws_form = sh.worksheet("숙제_응답")
    ws_study = sh.worksheet("학습_기록")
    ws_reflect = sh.worksheet("바이탈체크")

    all_values = ws_form.get_all_values()
    if len(all_values) <= 1:
        return 0

    new_count = 0
    for i, row in enumerate(all_values[1:], start=2):
        row = row + [""] * (14 - len(row))
        synced_mark = row[13]

        if synced_mark:
            continue

        (timestamp, name, target, achieved, read_count, dictation, vocab,
         gratitude, love, praise, overcome, curiosity, challenge, _) = row

        if not name:
            continue

        date_str = parse_timestamp_date(timestamp)

        ws_study.append_row([date_str, name, target, achieved, read_count, dictation, vocab])
        ws_reflect.append_row([date_str, name, gratitude, love, praise, overcome, curiosity, challenge])
        ws_form.update_cell(i, 14, "완료")
        new_count += 1

        # 폼으로 들어온 감사한 일도 공개 게시판에 자동 공유
        if gratitude and gratitude.strip():
            add_gratitude_post(name, gratitude.strip())

    return new_count

