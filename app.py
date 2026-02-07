import streamlit as st
from openai import OpenAI as OpenAIClient  # 이름 충돌 방지

MODEL_NAME = "gpt-4.1-mini"

SYSTEM_PROMPT = """
너는 '계획을 시작하기 어려운 사람'을 돕는 계획 보조 도구다.
사용자가 입력한 큰 목표를 '2~10분 이내의 아주 작은 첫 행동 1개'로 바꿔라.
조건:
1) 2~10분 이내
2) 준비물/전문지식 불필요
3) 실패 가능성 매우 낮게
4) 첫 행동 1개만
5) 설명 없이 한국어 한 문장만
""".strip()

def generate_micro_action(api_key: str, goal: str) -> str:
    client = OpenAIClient(api_key=api_key)
    resp = client.responses.create(
        model=MODEL_NAME,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f'목표: "{goal}"'}
        ],
    )
    return (resp.output_text() or "").strip()

st.set_page_config(page_title="2MIN PLAN", page_icon="✅", layout="wide")
st.title("✅ 2MIN PLAN")

if "micro_action" not in st.session_state:
    st.session_state.micro_action = "아직 생성된 행동이 없습니다."
if "done" not in st.session_state:
    st.session_state.done = False

st.sidebar.header("🔑 OpenAI API Key")
api_key = st.sidebar.text_input("OPENAI_API_KEY", type="password")

st.sidebar.divider()
st.sidebar.header("📌 오늘의 한 단계")
st.sidebar.success(st.session_state.micro_action)
if st.session_state.done:
    st.sidebar.info("좋습니다. 이 정도면 충분합니다 🙂")

goal = st.text_input("오늘의 큰 목표", placeholder="예: 기말고사 공부 / 운동 시작 / 방 정리")

col1, col2 = st.columns(2)
with col1:
    if st.button("계획 쪼개기"):
        if not api_key.strip():
            st.error("사이드바에 API Key를 입력해 주세요.")
        elif not goal.strip():
            st.warning("목표를 입력해 주세요.")
        else:
            try:
                st.session_state.micro_action = generate_micro_action(api_key.strip(), goal.strip())
                st.session_state.done = False
                st.rerun()
            except Exception as e:
                st.error(f"API 오류: {e}")

with col2:
    if st.button("✅ 완료"):
        st.session_state.done = True
        st.rerun()
