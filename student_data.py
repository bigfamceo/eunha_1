import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import re
import os

# ===== 초기 설정 =====
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
JSON_KEY_PATH = "json key/eunha-1.json"
SHEET_NAME = "eunha1"


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


# ===== 5. 바이탈체크(학생 소감) 추가/조회 (긍정심리학 6항목) =====
def add_student_reflection(name, gratitude, love, praise, overcome, curiosity, challenge):
    """학생이 직접 작성하는 소감 (긍정심리학 6항목)"""
    sh = get_spreadsheet()
    ws = sh.worksheet("바이탈체크")
    today = datetime.now().strftime("%Y-%m-%d")
    ws.append_row([today, name, gratitude, love, praise, overcome, curiosity, challenge])


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


# ===== 6. 구글폼 응답 동기화 =====
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

    return new_count

