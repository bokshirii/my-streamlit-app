import streamlit as st
from openai import OpenAI

# ----------------------------
# Config (고정)
# ----------------------------
MODEL_NAME = "gpt-4.1-mini"  # 계정에 따라 바꿔도 됨 (고정값)

SYSTEM_PROMPT = """너는 계획을 잘게 쪼개는 보조 도구다.

사용자가 입력한 목표를
“오늘 당장 시작할 수 있는 아주 작은 행동 1개”로 바꿔라.

조건:
1. 행동은 5~10분 이내에 끝낼 수 있어야 한다.
2. 특별한 준비물이나 전문 지식이 없어야 한다.
3. 실패할 가능성이 매우 낮아야 한다.
4. 계획 전체가 아니라 ‘첫 행동’만 제안해야 한다.
5. 설명은 하지 말고, 행동만 한 문장으로 제시하라.
"""

def generate_micro_action(api_key: str, goal: str) -> str:
    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=MODEL_NAME,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f'목표: "{goal}"'}
        ],
    )

    return (response.output_text() or "").strip()

# ----------------------------
# UI
# ----------------------------
st.set_page_config(page_title="2MIN PLAN", page_icon="✅", layout="wide")
st.title("✅ 2MIN PLAN")
st.caption("큰 목표를 오늘 당장 가능한 아주 작은 행동 1개로 바꿔줍니다.")

# session state
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "micro_action" not in st.session_state:
    st.session_state.micro_action = "아직 생성된 행동이 없습니다."
if "done" not in st.session_state:
    st.session_state.done = False

# ----------------------------
# Sidebar (API Key + 결과)
# ----------------------------
st.sidebar.header("🔑 OpenAI API Key")

st.session_state.api_key = st.sidebar.text_input(
    "OPENAI_API_KEY",
    type="password",
    help="데모용 입력 방식입니다. 실제 배포 시에는 Secrets 사용 권장"
)

st.sidebar.divider()
st.sidebar.header("📌 오늘의 한 단계")
st.sidebar.success(st.session_state.micro_action)

if st.session_state.done:
    st.sidebar.info("좋습니다. 이 정도면 충분합니다 🙂")

# ----------------------------
# Main
# ----------------------------
goal = st.text_input(
    "큰 목표를 입력하세요",
    placeholder="예: 기말고사 공부 / 운동 시작 / 방 정리"
)

col1, col2 = st.columns(2)

with col1:
    if st.button("계획 쪼개기"):
        if not st.session_state.api_key.strip():
            st.error("사이드바에 OpenAI API Key를 입력하세요.")
        elif not goal.strip():
            st.warning("목표를 입력하세요.")
        else:
            with st.spinner("아주 작은 행동을 생성 중..."):
                try:
                    action = generate_micro_action(
                        st.session_state.api_key.strip(),
                        goal.strip()
                    )
                    if not action:
                        action = "목표를 조금 더 구체적으로 적어 주세요."
                    st.session_state.micro_action = action
                    st.session_state.done = False
                    st.rerun()
                except Exception as e:
                    st.error(f"API 오류: {e}")

with col2:
    if st.button("✅ 완료"):
        st.session_state.done = True
        st.rerun()

# ----------------------------
# 과제용 섹션
# ----------------------------
with st.expander("한계 및 고도화 방안"):
    st.write("- **한계**: AI가 제안한 행동이 항상 최적이라고 보장할 수 없으며, 사용자 상태나 과거 기록은 반영되지 않습니다.")
    st.write("- **고도화**: 실행 성공 데이터를 축적해 성공률이 높은 행동을 우선 추천하거나, 에너지 상태에 따라 행동 시간을 조절할 수 있습니다.")
