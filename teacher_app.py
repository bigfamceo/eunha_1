import streamlit as st
import student_data as sd
import report_generator as rg
from datetime import datetime

st.set_page_config(page_title="센터 교사관리", page_icon="👩‍🏫", layout="centered")

TEACHER_PASSWORD = "3004"

# ===== 미니멀 디자인 CSS =====
MINIMAL_CSS = """
<style>
    .block-container {padding-top: 2.5rem; padding-bottom: 3rem; max-width: 860px;}
    h1, h2, h3, h4 {font-weight: 700; letter-spacing: -0.5px;}
    [data-testid="stCaptionContainer"] {color: #9CA3AF !important;}
    div[data-testid="stMetric"] {
        background-color: #F7F7F5;
        border: 1px solid #ECECE9;
        border-radius: 12px;
        padding: 14px 18px;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px !important;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
    }
    .stButton>button[kind="primary"] {
        background-color: #0F766E;
        border-color: #0F766E;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
    }
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stNumberInput"] input {
        border-radius: 8px;
    }
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
    }
    section[data-testid="stSidebar"] {
        background-color: #F7F7F5;
    }
</style>
"""
st.markdown(MINIMAL_CSS, unsafe_allow_html=True)


def badge(text, color):
    """색깔 배지 HTML 생성"""
    return (
        f"<span style='background:{color}1A;color:{color};padding:3px 10px;"
        f"border-radius:6px;font-size:0.85em;font-weight:600;'>{text}</span>"
    )


# ===== 세션 상태 초기화 =====
if "teacher_logged_in" not in st.session_state:
    st.session_state.teacher_logged_in = False


# ===== 교사 로그인 화면 =====
def show_teacher_login():
    st.write("")
    st.write("")

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown(
            "<h1 style='text-align:center; margin-bottom:0;'>👩‍🏫 센터 교사관리</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; color:#9CA3AF; margin-top:4px;'>"
            "학생 학습 현황과 피드백을 관리하세요</p>",
            unsafe_allow_html=True,
        )
        st.write("")

        with st.container(border=True):
            password = st.text_input("비밀번호", type="password")
            st.write("")

            if st.button("로그인", use_container_width=True, type="primary"):
                if password == TEACHER_PASSWORD:
                    st.session_state.teacher_logged_in = True
                    st.rerun()
                else:
                    st.error("비밀번호가 올바르지 않습니다.")


# ===== 학생 목록 불러오기 =====
def get_student_list():
    sh = sd.get_spreadsheet()
    ws = sh.worksheet("학생_명부")
    records = ws.get_all_records(expected_headers=["학생ID", "이름", "학년", "비밀번호"])
    return [row["이름"] for row in records]


# ===== 교사 메인 화면 =====
def show_teacher_main():
    with st.sidebar:
        st.markdown("### 👩‍🏫 센터 교사관리")
        st.write("")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.teacher_logged_in = False
            st.rerun()

        st.divider()
        student_names = get_student_list()
        selected_student = st.selectbox("학생 선택", student_names)

        st.write("")
        if st.button("🔄 구글폼 새 응답 가져오기", use_container_width=True):
            count = sd.sync_form_responses()
            if count > 0:
                st.success(f"새 응답 {count}건 반영 완료!")
            else:
                st.info("새로운 응답이 없어요.")

    st.markdown("#### 👩‍🏫 센터 교사관리")
    st.write("")

    if not selected_student:
        return

    with st.container(border=True):
        st.markdown(f"#### 📋 {selected_student} 학생 현황")

    st.write("")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 학습 기록", "💭 바이탈체크", "✍️ 주간 피드백 작성", "📅 월말 보고서"])

    with tab1:
        records = sd.get_study_records(selected_student)
        if records:
            records_sorted = sorted(records, key=lambda r: r["날짜"], reverse=True)
            recent = records_sorted[:3]
            rest = records_sorted[3:]

            for r in recent:
                with st.container(border=True):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.write(f"**{r['날짜']}**")
                        dict_badge = badge("딕테이션 완료", "#0F766E") if r["딕테이션"] == "O" else badge("딕테이션 미완료", "#9CA3AF")
                        vocab_badge = badge("어휘 완료", "#0F766E") if r["어휘"] == "O" else badge("어휘 미완료", "#9CA3AF")
                        st.markdown(f"{dict_badge} &nbsp; {vocab_badge}", unsafe_allow_html=True)
                    with col2:
                        st.caption(f"읽은 횟수: {r['읽은횟수']}회")
                        st.caption(f"목표 {r['리딩_목표시간']}초 → 성취 {r['리딩_성취시간']}초")

            if rest:
                st.write("")
                with st.expander(f"이전 기록 더보기 ({len(rest)}건)"):
                    st.dataframe(rest, use_container_width=True, hide_index=True)
        else:
            st.info("아직 학습 기록이 없어요.")

    with tab2:
        reflections = sd.get_student_reflections(selected_student)
        if reflections:
            reflections_sorted = sorted(reflections, key=lambda r: r["작성일자"], reverse=True)
            for r in reflections_sorted:
                with st.container(border=True):
                    st.caption(r["작성일자"])
                    st.write(f"**감사한 일:** {r['감사한_일']}")
                    st.write(f"**사랑을 경험한 일:** {r['사랑을_경험한_일']}")
                    st.write(f"**칭찬/격려한 일:** {r['남을_칭찬하거나_격려한_일']}")
                    st.write(f"**역경 극복한 일:** {r['역경을_극복한_일']}")
                    st.write(f"**호기심/궁금했던 점:** {r['호기심_궁금했던_점']}")
                    st.write(f"**도전해 본 일:** {r['도전해_본_일']}")
        else:
            st.info("아직 작성된 바이탈체크가 없어요.")

    with tab3:
        with st.container(border=True):
            st.write("이번 주 피드백을 작성해주세요.")

            feedback_date = st.date_input("기록 날짜", value=datetime.now())
            week_num = (feedback_date.day - 1) // 7 + 1
            week = f"{week_num}주차"
            st.caption(f"자동 계산된 주차: {week}")

            content = st.text_area("피드백 내용", height=150)

            if st.button("피드백 저장하기", use_container_width=True, type="primary"):
                if not content:
                    st.warning("피드백 내용을 입력해주세요.")
                else:
                    sd.add_teacher_feedback(selected_student, week, content, feedback_date)
                    st.success("피드백이 저장되었어요!")

        st.write("")
        st.markdown("**지난 피드백 목록**")
        feedbacks = sd.get_teacher_feedback(selected_student)
        if feedbacks:
            feedbacks_sorted = sorted(feedbacks, key=lambda r: r["작성일자"], reverse=True)
            for f in feedbacks_sorted:
                with st.container(border=True):
                    st.caption(f"{f['작성일자']} · {f['주차']}")
                    st.write(f['교사_피드백'])
        else:
            st.info("아직 작성된 피드백이 없어요.")

    with tab4:
        st.write("월별 학습 리포트를 확인하고 PDF로 다운로드하세요.")

        col1, col2 = st.columns(2)
        with col1:
            year = st.number_input("연도", min_value=2020, max_value=2100, value=datetime.now().year)
        with col2:
            month = st.number_input("월", min_value=1, max_value=12, value=datetime.now().month)

        if st.button("보고서 생성", use_container_width=True, type="primary"):
            records, reflections, feedbacks, stats = rg.get_monthly_stats(selected_student, int(year), int(month))

            st.markdown(f"#### 📊 {selected_student} 학생 {year}년 {month}월 학습 요약")
            c1, c2, c3 = st.columns(3)
            c1.metric("🗓️ 총 학습일수", f"{stats['총_학습일수']}일")
            c2.metric("🎯 목표 달성", f"O {stats['목표달성_O']} / X {stats['목표달성_X']}")
            c3.metric("📖 총 읽은 횟수", f"{stats['총_읽은횟수']}회")
            c4, c5 = st.columns(2)
            c4.metric("🎧 딕테이션 성공률", f"{stats['딕테이션_성공률']}%")
            c5.metric("📚 어휘 성공률", f"{stats['어휘_성공률']}%")

            st.write("")
            st.markdown("**✍️ 교사 피드백**")
            if feedbacks:
                for f in feedbacks:
                    with st.container(border=True):
                        st.caption(f"{f['작성일자']} · {f['주차']}")
                        st.write(f['교사_피드백'])
            else:
                st.info("작성된 피드백이 없어요.")

            st.write("")
            st.markdown("**💭 바이탈체크**")
            if reflections:
                for r in reflections:
                    with st.container(border=True):
                        st.caption(r["작성일자"])
                        st.write(f"**감사한 일:** {r['감사한_일']}")
                        st.write(f"**사랑을 경험한 일:** {r['사랑을_경험한_일']}")
                        st.write(f"**칭찬/격려한 일:** {r['남을_칭찬하거나_격려한_일']}")
                        st.write(f"**역경 극복한 일:** {r['역경을_극복한_일']}")
                        st.write(f"**호기심/궁금했던 점:** {r['호기심_궁금했던_점']}")
                        st.write(f"**도전해 본 일:** {r['도전해_본_일']}")
            else:
                st.info("작성된 바이탈체크가 없어요.")

            pdf_bytes = rg.generate_pdf(selected_student, int(year), int(month))
            st.download_button(
                label="📄 PDF로 다운로드",
                data=pdf_bytes,
                file_name=f"{selected_student}_{year}년{month}월_리포트.pdf",
                mime="application/pdf",
                use_container_width=True
            )


# ===== 화면 분기 =====
if st.session_state.teacher_logged_in:
    show_teacher_main()
else:
    show_teacher_login()