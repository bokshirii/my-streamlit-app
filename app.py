import streamlit as st
from openai import OpenAI as OpenAIClient

MODEL_NAME = "gpt-4.1-mini"

st.set_page_config(page_title="2MIN PLAN", layout="centered")

if "micro_action" not in st.session_state:
    st.session_state.micro_action = ""
if "done" not in st.session_state:
    st.session_state.done = False


def generate_micro_action(api_key: str, goal: str) -> str:
    system_prompt = (
        "너는 실행 가능한 아주 작은 첫 행동을 제안하는 코치다. "
        "조건을 엄격히 지켜라."
    )
    user_prompt = (
        "다음 목표에 대해 2~10분 이내에 끝낼 수 있는 아주 작은 첫 행동 1개만 제안해줘. "
        "준비물이나 전문지식이 필요 없어야 하고 실패 가능성이 매우 낮아야 해. "
        "설명 없이 한국어 한 문장만 출력해줘.\n\n"
        f"목표: {goal.strip()}"
    )
    client = OpenAIClient(api_key=api_key)
    response = client.responses.create(
        model=MODEL_NAME,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    text = (response.output_text or "").strip()
    first_line = text.splitlines()[0] if text else ""
    return first_line.strip()


st.title("2MIN PLAN")

api_key = st.sidebar.text_input("OpenAI API Key", type="password")

st.sidebar.subheader("📌 오늘의 한 단계")
if st.session_state.micro_action:
    st.sidebar.write(st.session_state.micro_action)
else:
    st.sidebar.write("아직 추천 행동이 없습니다.")

if st.session_state.done:
    st.sidebar.write("좋습니다. 이 정도면 충분합니다 🙂")

goal = st.text_input("큰 목표를 입력하세요", placeholder="예: 영어 공부를 꾸준히 하고 싶다")

col1, col2 = st.columns(2)

with col1:
    if st.button("계획 쪼개기", type="primary"):
        if not goal.strip():
            st.warning("목표를 입력해주세요.")
        elif not api_key.strip():
            st.error("OpenAI API Key를 입력해주세요.")
        else:
            st.session_state.micro_action = generate_micro_action(api_key, goal)
            st.session_state.done = False
            st.rerun()

with col2:
    if st.button("✅ 완료"):
        st.session_state.done = True
        st.rerun()

if st.session_state.micro_action:
    st.write(st.session_state.micro_action)

if st.session_state.done:
    st.write("좋습니다. 이 정도면 충분합니다 🙂")
