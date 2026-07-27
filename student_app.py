import streamlit as st
import student_data as sd

st.set_page_config(page_title="센터 학습관리", page_icon="📚")

# ===== 세션 상태 초기화 =====
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "student_info" not in st.session_state:
    st.session_state.student_info = None


# ===== 로그인 화면 =====
def show_login():
    st.title("📚 센터 학습관리")
    st.subheader("로그인")

    name = st.text_input("이름")
    password = st.text_input("비밀번호", type="password")

    if st.button("로그인", use_container_width=True):
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
    st.subheader("📝 오늘 학습 기록")

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

    st.divider()
    st.subheader("💭 바이탈체크")

    gratitude = st.text_area("감사한 일")
    love = st.text_area("사랑을 경험한 일")
    praise = st.text_area("남을 칭찬하거나 격려한 일")
    overcome = st.text_area("역경을 극복한 일")
    curiosity = st.text_area("오늘 호기심이나 궁금했던 점")
    challenge = st.text_area("오늘 도전해 본 일")

    if st.button("오늘 기록 저장하기", use_container_width=True):
        sd.add_study_record(name, target_time, achieved_time, read_count, dictation, vocab)
        sd.add_student_reflection(name, gratitude, love, praise, overcome, curiosity, challenge)
        st.success("✅ 오늘의 학습 기록과 바이탈체크가 저장되었어요!")


# ===== 탭 2: 내 기록 보기 (학습 기록 + 바이탈체크 통합) =====
def tab_view_records(name):
    st.subheader("📊 내 학습 기록")

    records = sd.get_study_records(name)
    if records:
        records_sorted = sorted(records, key=lambda r: r["날짜"], reverse=True)
        st.dataframe(records_sorted, use_container_width=True)
    else:
        st.info("아직 기록된 학습 내용이 없어요.")

    st.divider()
    st.subheader("💭 내 바이탈체크")

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


# ===== 로그인 후 메인 화면 =====
def show_main():
    info = st.session_state.student_info
    name = info["이름"]

    st.title(f"👋 안녕하세요, {name}님!")
    st.caption(f"학년: {info['학년']}")

    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.student_info = None
        st.rerun()

    st.divider()

    tab1, tab2 = st.tabs(["📝 오늘 기록하기", "📊 내 기록 보기"])

    with tab1:
        tab_add_record(name)
    with tab2:
        tab_view_records(name)


# ===== 화면 분기 =====
if st.session_state.logged_in:
    show_main()
else:
    show_login()

    