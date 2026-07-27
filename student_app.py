import streamlit as st
import student_data as sd
from datetime import datetime

st.set_page_config(page_title="센터 학습관리", page_icon="📚", layout="centered")

WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]

# ===== 미니멀 디자인 CSS =====
MINIMAL_CSS = """
<style>
    .block-container {padding-top: 2.5rem; padding-bottom: 3rem; max-width: 760px;}
    h1, h2, h3, h4 {font-weight: 700; letter-spacing: -0.5px;}
    [data-testid="stCaptionContainer"] {color: #9CA3AF !important;}
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
    .rank-row {display:flex; align-items:center; padding:10px 12px; border-radius:10px; margin-bottom:6px; background:#F7F7F5;}
    .rank-row.r1 {background:#FFF6DA; border:1px solid #FFD966;}
    .rank-row.r2 {background:#F2F2F2; border:1px solid #CCCCCC;}
    .rank-row.r3 {background:#FBE9DD; border:1px solid #E0B088;}
    .rank-badge {width:32px; font-weight:700; font-size:16px; text-align:center;}
    .rank-name {flex:1; padding-left:8px; font-size:15px;}
    .rank-point {font-weight:700; color:#0F766E; font-size:15px;}
</style>
"""
st.markdown(MINIMAL_CSS, unsafe_allow_html=True)


def badge(text, color):
    """색깔 배지 HTML 생성"""
    return (
        f"<span style='background:{color}1A;color:{color};padding:3px 10px;"
        f"border-radius:6px;font-size:0.85em;font-weight:600;'>{text}</span>"
    )


def today_korean():
    today = datetime.now()
    return f"{today.year}년 {today.month}월 {today.day}일 ({WEEKDAY_KR[today.weekday()]})"


def medal(rank):
    return {0: "🥇", 1: "🥈", 2: "🥉"}.get(rank, str(rank + 1))


def render_board(data):
    if not data:
        st.info("아직 기록이 없어요.")
        return
    html = ""
    for i, item in enumerate(data):
        cls = f"r{i+1}" if i < 3 else ""
        html += (
            f'<div class="rank-row {cls}">'
            f'<div class="rank-badge">{medal(i)}</div>'
            f'<div class="rank-name">{item["name"]}</div>'
            f'<div class="rank-point">{item["points"]}점</div>'
            f'</div>'
        )
    st.markdown(html, unsafe_allow_html=True)


# ===== 세션 상태 초기화 =====
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "student_info" not in st.session_state:
    st.session_state.student_info = None


# ===== 로그인 화면 =====
def show_login():
    st.write("")
    st.write("")

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown(
            "<h1 style='text-align:center; margin-bottom:0;'>📚 센터 학습관리</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; color:#9CA3AF; margin-top:4px;'>"
            "오늘의 학습을 기록하고 나의 성장을 확인해보세요</p>",
            unsafe_allow_html=True,
        )
        st.write("")

        with st.container(border=True):
            name = st.text_input("이름")
            password = st.text_input("비밀번호", type="password")
            st.write("")

            if st.button("로그인", use_container_width=True, type="primary"):
                if not name or not password:
                    st.warning("이름과 비밀번호를 모두 입력해주세요.")
                    return

                result = sd.login(name, password)
                if result:
                    st.session_state.logged_in = True
                    st.session_state.student_info = result
                    st.rerun()
                else:
                    st.error("이름 또는 비밀번호가 올바르지 않습니다.")


# ===== 탭 1: 오늘 기록하기 (학습 기록 + 바이탈체크 통합) =====
def tab_add_record(name):
    with st.container(border=True):
        st.markdown("#### 📝 오늘 학습 기록")

        col1, col2 = st.columns(2)
        with col1:
            target_time = st.number_input("리딩 목표시간 (초)", min_value=0, step=10)
        with col2:
            achieved_time = st.number_input("리딩 성취시간 (초)", min_value=0, step=10)

        read_count = st.number_input("읽은 횟수", min_value=0, step=1)

        col3, col4 = st.columns(2)
        with col3:
            dictation = st.selectbox("딕테이션", ["O", "X"])
        with col4:
            vocab = st.selectbox("어휘", ["O", "X"])

    st.write("")

    with st.container(border=True):
        st.markdown("#### 💭 바이탈체크")
        st.caption("감사한 일은 자동으로 '감사나눔' 게시판에도 공유돼요.")

        gratitude = st.text_area("감사한 일")
        love = st.text_area("사랑을 경험한 일")
        praise = st.text_area("남을 칭찬하거나 격려한 일")
        overcome = st.text_area("역경을 극복한 일")
        curiosity = st.text_area("오늘 호기심이나 궁금했던 점")
        challenge = st.text_area("오늘 도전해 본 일")

    st.write("")

    if st.button("✅ 오늘 기록 저장하기", use_container_width=True, type="primary"):
        sd.add_study_record(name, target_time, achieved_time, read_count, dictation, vocab)
        sd.add_student_reflection(name, gratitude, love, praise, overcome, curiosity, challenge)
        st.success("오늘의 학습 기록과 바이탈체크가 저장되었어요! 성실왕/감사왕 점수도 올라갔어요 🎉")


# ===== 탭 2: 내 기록 보기 (카드형 최근 기록 + 표) =====
def tab_view_records(name):
    st.markdown("#### 📊 내 학습 기록")

    records = sd.get_study_records(name)
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
        st.info("아직 기록된 학습 내용이 없어요.")

    st.write("")
    st.markdown("#### 💭 내 바이탈체크")

    reflections = sd.get_student_reflections(name)
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


# ===== 탭 3: 🏆 우리반 랭킹 (성실왕/감사왕 + 감사나눔) =====
def tab_ranking(name):
    my = sd.get_my_total_points(name)
    st.markdown(
        f"<div style='background:#0F766E1A; color:#0F766E; font-weight:700; "
        f"padding:8px 14px; border-radius:20px; display:inline-block; margin-bottom:14px;'>"
        f"🏅 나의 누적 {my['total']}점 (학습 {my['study']} + 감사 {my['vital']})</div>",
        unsafe_allow_html=True,
    )

    period_label = st.radio("기간", ["이번 주", "이번 달", "전체"], horizontal=True, label_visibility="collapsed")
    period_map = {"이번 주": "week", "이번 달": "month", "전체": "all"}
    period = period_map[period_label]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📚 성실왕")
        render_board(sd.get_study_ranking(period))
    with col2:
        st.markdown("#### 💝 감사왕")
        render_board(sd.get_vital_ranking(period))

    st.write("")
    st.markdown("#### 💌 감사나눔")
    st.caption("친구들이 적은 감사한 일이에요. 좋아요로 응원해주세요!")

    posts = sd.get_gratitude_posts(name)
    if not posts:
        st.info("아직 올라온 감사 글이 없어요.")
    else:
        for p in posts:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{p['name']}** &nbsp; <span style='color:#9CA3AF;font-size:0.85em;'>{p['date']}</span>", unsafe_allow_html=True)
                    st.write(p["content"])
                with col2:
                    if p["liked_by_me"]:
                        st.button(f"💖 {p['likes']}", key=f"like_{p['id']}", disabled=True, use_container_width=True)
                    else:
                        if st.button(f"🤍 {p['likes']}", key=f"like_{p['id']}", use_container_width=True):
                            sd.add_like(p["id"], name)
                            st.rerun()


# ===== 로그인 후 메인 화면 =====
def show_main():
    info = st.session_state.student_info
    name = info["이름"]

    with st.sidebar:
        st.markdown(f"### 👋 {name}님")
        st.caption(f"학년: {info['학년']}")
        st.write("")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.student_info = None
            st.rerun()

    with st.container(border=True):
        st.markdown(f"#### 👋 안녕하세요, {name}님!")
        st.caption(today_korean())

    st.write("")

    tab1, tab2, tab3 = st.tabs(["📝 오늘 기록하기", "📊 내 기록 보기", "🏆 우리반 랭킹"])

    with tab1:
        tab_add_record(name)
    with tab2:
        tab_view_records(name)
    with tab3:
        tab_ranking(name)


# ===== 화면 분기 =====
if st.session_state.logged_in:
    show_main()
else:
    show_login()