import os
import streamlit as st
from openai import OpenAI

# ----------------------------
# Config
# ----------------------------
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")  # 계정/권한에 맞게 바꾸세요.
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """너는 계획을 잘게 쪼개는 보조 도구다.

사용자가 입력한 목표를 “오늘 당장 시작할 수 있는 아주 작은 행동 1개”로 바꿔라.

조건:
1. 행동은 5~10분 이내에 끝낼 수 있어야 한다.
2. 특별한 준비물이나 전문 지식이 없어야 한다.
3. 실패할 가능성이 매우 낮아야 한다.
4. 계획 전체가 아니라 ‘첫 행동’만 제안해야 한다.
5. 설명은 하지 말고, 행동만 한 문장으로 제시하라.
"""

def generate_micro_action(goal: str, model: str) -> str:
    """Call OpenAI and return a single-sentence action."""
    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f'목표: "{goal}"'}
        ],
    )
    # openai-python responses 객체는 output_text()로 텍스트를 간단히 뽑을 수 있습니다.
    # (문서/예제 참고)
    return (resp.output_text() or "").strip()

# ----------------------------
# UI
# ----------------------------
st.set_page_config(page_title="2MIN PLAN", page_icon="✅", layout="wide")
st.title("✅ 2MIN PLAN (MVP)")
st.caption("큰 목표를 ‘오늘 당장 가능한 아주 작은 행동 1개’로 바꿔줍니다.")

# Sidebar (결과를 여기 띄움)
st.sidebar.header("📌 오늘의 한 단계")

if "micro_action" not in st.session_state:
    st.session_state.micro_action = "아직 생성된 행동이 없습니다."
if "done" not in st.session_state:
    st.session_state.done = False

# Main inputs
with st.form("goal_form", clear_on_submit=False):
    goal = st.text_input("큰 목표를 입력하세요", placeholder="예: 기말고사 공부 / 운동 시작 / 방 정리")
    model = st.text_input("모델(선택)", value=DEFAULT_MODEL)
    submitted = st.form_submit_button("계획 쪼개기")

if submitted:
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    elif not goal.strip():
        st.warning("목표를 입력해 주세요.")
    else:
        with st.spinner("아주 작은 행동을 만드는 중..."):
            try:
                micro = generate_micro_action(goal.strip(), model.strip())
                if not micro:
                    micro = "목표를 더 구체적으로 한 문장으로 적어주세요. (예: '기말고사 1과목 1단원 공부 시작')"
                st.session_state.micro_action = micro
                st.session_state.done = False
            except Exception as e:
                st.error(f"API 호출 오류: {e}")

# Sidebar output
st.sidebar.success(st.session_state.micro_action)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("✅ 완료"):
        st.session_state.done = True
with col2:
    if st.button("🔄 다시 추천"):
        # 같은 목표라도 다시 뽑고 싶을 때: 목표를 재제출하는 UX 대신 간단히 재호출
        if goal.strip() and os.getenv("OPENAI_API_KEY"):
            with st.spinner("다시 추천 중..."):
                try:
                    st.session_state.micro_action = generate_micro_action(goal.strip(), model.strip())
                    st.session_state.done = False
                except Exception as e:
                    st.error(f"API 호출 오류: {e}")

if st.session_state.done:
    st.sidebar.info("좋습니다. 이 정도면 충분합니다 🙂")

# Minimal “한계/고도화” 섹션(과제용)
with st.expander("한계 및 고도화 방안(과제용)"):
    st.write("- **한계**: AI 제안이 항상 사용자에게 최적이라고 보장할 수 없고, 현재는 사용자의 컨디션/과거 데이터 반영이 제한적입니다.")
    st.write("- **고도화**: 완료/미완료 기록을 축적해 성공률이 높은 행동을 우선 추천하거나, 에너지 상태(피곤/보통/집중)에 따라 5/10/15분 버전으로 자동 조절할 수 있습니다.")
