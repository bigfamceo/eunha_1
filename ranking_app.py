import streamlit as st
import student_data as sd

st.set_page_config(page_title="우리반 랭킹", page_icon="🏆", layout="centered")

MINIMAL_CSS = """
<style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 760px;}
    h1, h2, h3, h4 {font-weight: 700; letter-spacing: -0.5px;}
    div[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 14px !important;}
    .stButton>button {border-radius: 8px; font-weight: 500;}
    .stButton>button[kind="primary"] {background-color: #0F766E; border-color: #0F766E;}
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


# ===== 상단: 이름 선택 (좋아요 누르기 / 내 점수 확인용) =====
st.markdown("<h1 style='text-align:center; margin-bottom:0;'>🏆 우리 반 랭킹</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color:#9CA3AF; margin-top:4px;'>학습일지 100점 + 바이탈체크 100점, 매일 쌓아가요!</p>",
    unsafe_allow_html=True,
)
st.write("")

if "viewer_name" not in st.session_state:
    st.session_state.viewer_name = ""

names = sd.get_all_student_names()
options = [""] + names
selected = st.selectbox(
    "내 이름 (좋아요를 누르거나 내 점수를 보려면 선택하세요)",
    options,
    index=options.index(st.session_state.viewer_name) if st.session_state.viewer_name in options else 0,
)
st.session_state.viewer_name = selected

if selected:
    my = sd.get_my_total_points(selected)
    st.markdown(
        f"<div style='background:#0F766E1A; color:#0F766E; font-weight:700; "
        f"padding:8px 14px; border-radius:20px; display:inline-block; margin-bottom:10px;'>"
        f"🏅 {selected} 누적 {my['total']}점 (학습 {my['study']} + 감사 {my['vital']})</div>",
        unsafe_allow_html=True,
    )

st.write("")

tab1, tab2 = st.tabs(["🏆 랭킹보드", "💌 감사나눔"])

# ===== 탭 1: 랭킹보드 =====
with tab1:
    period_label = st.radio("기간", ["이번 주", "이번 달", "전체"], horizontal=True, label_visibility="collapsed")
    period_map = {"이번 주": "week", "이번 달": "month", "전체": "all"}
    period = period_map[period_label]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📚 성실왕 (학습일지)")
        render_board(sd.get_study_ranking(period))
    with col2:
        st.markdown("#### 💝 감사왕 (바이탈체크)")
        render_board(sd.get_vital_ranking(period))

# ===== 탭 2: 감사나눔 게시판 =====
with tab2:
    st.caption("바이탈체크에 적은 '감사한 일'이 자동으로 여기에 올라와요. 서로 좋아요를 눌러주세요!")
    posts = sd.get_gratitude_posts(st.session_state.viewer_name or None)

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
                            if not st.session_state.viewer_name:
                                st.warning("먼저 이름을 선택해주세요!")
                            else:
                                sd.add_like(p["id"], st.session_state.viewer_name)
                                st.rerun()

                                