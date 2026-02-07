import streamlit as st
from openai import OpenAI

# =========================
# 2MIN PLAN - MVP
# =========================

MODEL_NAME = "gpt-4.1-mini"  # 모델은 고정 (UI에서 입력받지 않음)

SYSTEM_PROMPT = """
너는 '계획을 시작하기 어려운 사람'을 돕는 계획 보조 도구다.

사용자가 입력한 큰 목표를
'오늘 당장 시작할 수 있는 아주 작은 행동 1개'로 바꿔라.

조건:
1) 2~10분 이내로 끝낼 수 있어야 한다.
2) 특별한 준비물/전문 지식이 필요하면 안 된다.
3) 실패 가능성이 매우 낮아야 한다.
4) 계획 전체가 아니라 '첫 행동'만 제시한다.
5) 설명하지 말고, 행동만 한국어 한 문장으로 출력한다.
""".strip()

def generate_micro_action(api_key: str, goal: str) -> str:
    client = OpenAI(api_key=api_key)

    resp = client.responses.create(
        model=MODEL_NAME,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f'목표: "{goal}"'}
        ],
    )

    return (resp.output_text() or "").strip()


# -------------------------
# UI
# -------------------------
st.set_page_config(page_title="2MIN PLAN", page_icon="✅", layout="wide")
st.title("✅ 2MIN PLAN")
st.caption("큰 계획을 ‘오늘 당장 가능한 아주 작은 행동 1개’로 바꿔드립니다.")

# session state
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "micro_action" not in st.session_state:
    st.session_state.micro_action = "아직 생성된 행동이 없습니다."
if "done" not in st.session_state:
    st.session_state.done = False

# Sidebar: API Key + Output
st.sidebar.header("🔑 OpenAI API Key")
st.session_state.api_key = st.sidebar.text_input(
    "OPENAI_API_KEY",
    type="password",
    help="과제/MVP 데모용 입력 방식입니다."
)

st.sidebar.divider()
st.sidebar.header("📌 오늘의 한 단계")
st.sidebar.success(st.session_state.micro_action)

if st.session_state.done:
    st.sidebar.info("좋습니다. 이 정도면 충분합니다 🙂")

# Main: goal input
goal = st.text_input(
    "오늘의 큰 목표를 입력하세요",
    placeholder="예: 기말고사 공부 / 운동 시작 / 방 정리"
)

col1, col2 = st.columns(2)

with col1:
    if st.button("계획 쪼개기"):
        if not st.session_state.api_key.strip():
            st.error("사이드바에 OpenAI API Key를 입력해 주세요.")
        elif not goal.strip():
            st.warning("목표를 입력해 주세요.")
        else:
            with st.spinner("아주 작은 행동을 생성 중..."):
                try:
                    action = generate_micro_action(
                        api_key=st.session_state.api_key.strip(),
                        goal=goal.strip()
                    )
                    if not action:
                        action = "목표를 조금 더 구체적으로 적어 주세요. (예: '기말고사 1단원 시작')"
                    st.session_state.micro_action = action
                    st.session_state.done = False
                    st.rerun()
                except Exception as e:
                    st.error(f"API 오류: {e}")

with col2:
    if st.button("✅ 완료"):
        st.session_state.done = True
        st.rerun()
