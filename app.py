import streamlit as st
from openai import OpenAI

# ----------------------------
# Prompts / Logic
# ----------------------------
SYSTEM_PROMPT = """너는 계획을 잘게 쪼개는 보조 도구다.

사용자가 입력한 목표를 “오늘 당장 시작할 수 있는 아주 작은 행동 1개”로 바꿔라.

조건:
1. 행동은 5~10분 이내에 끝낼 수 있어야 한다.
2. 특별한 준비물이나 전문 지식이 없어야 한다.
3. 실패할 가능성이 매우 낮아야 한다.
4. 계획 전체가 아니라 ‘첫 행동’만 제안해야 한다.
5. 설명은 하지 말고, 행동만 한 문장으로 제시하라.
"""

def generate_micro_action(api_key: str, model: str, goal: str) -> str:
    """Create client with user-provided key and generate a single-sentence action."""
    client = OpenAI(api_key=api_key)

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f'목표: "{goal}"'}
        ],
    )
    return (resp.output_text() or "").strip()

# ----------------------------
# UI
# ----------------------------
st.set_page_config(page_title="2MIN PLAN", page_icon="✅", layout="wide")
st.title("✅ 2MIN PLAN (MVP)")
st.caption("큰 목표를 ‘오늘 당장 가능한 아주 작은 행동 1개’로 바꿔줍니다.")

# Session state init
if "micro_action" not in st.session_state:
    st.session_state.micro_action = "아직 생성된 행동이 없습니다."
if "done" not in st.session_state:
    st.session_state.done = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "model" not in st.session_state:
    st.session_state.model = "gpt-5.2"  # 필요시 본인 계정에서 가능한 모델로 변경

# ----------------------------
# Sidebar: API Key + Result
# ----------------------------
st.sidebar.header("🔑 OpenAI 설정")

st.session_state.api_key = st.sidebar.text_input(
    "OPENAI_API_KEY (비밀번호 입력)",
    value=st.session_state.api_key,
    type="password",
    help="데모용 입력 방식입니다. 배포 시에는 Streamlit Secrets 사용을 권장합니다."
)

st.session_state.model = st.sidebar.text_input(
    "모델",
    value=st.session_state.model
)

st.sidebar.divider()
st.sidebar.header("📌 오늘의 한 단계")
st.sidebar.success(st.session_state.micro_action)

if st.session_state.done:
    st.sidebar.info("좋습니다. 이 정도면 충분합니다 🙂")

# ----------------------------
# Main area
# ----------------------------
goal = st.text_input("큰 목표를 입력하세요", placeholder="예: 기말고사 공부 / 운동 시작 / 방 정리")

colA, colB = st.columns([1, 1])

with colA:
    if st.button("계획 쪼개기"):
        if not st.session_state.api_key.strip():
            st.error("사이드바에 OPENAI_API_KEY를 먼저 입력해 주세요.")
        elif not goal.strip():
            st.warning("목표를 입력해 주세요.")
        else:
            with st.spinner("아주 작은 행동을 만드는 중..."):
                try:
                    micro = generate_micro_action(
                        api_key=st.session_state.api_key.strip(),
                        model=st.session_state.model.strip(),
                        goal=goal.strip()
                    )
                    if not micro:
                        micro = "목표를 더 구체적으로 한 문장으로 적어주세요. (예: '기말고사 1과목 1단원 시작')"
                    st.session_state.micro_action = micro
                    st.session_state.done = False
                    st.rerun()
                except Exception as e:
                    st.error(f"API 호출 오류: {e}")

with colB:
    if st.button("✅ 완료"):
        st.session_state.done = True
        st.rerun()

# (선택) 재추천 버튼
if st.button("🔄 다시 추천"):
    if not st.session_state.api_key.strip():
        st.error("사이드바에 OPENAI_API_KEY를 먼저 입력해 주세요.")
    elif not goal.strip():
        st.warning("목표를 입력해 주세요.")
    else:
        with st.spinner("다시 추천 중..."):
            try:
                st.session_state.micro_action = generate_micro_action(
                    api_key=st.session_state.api_key.strip(),
                    model=st.session_state.model.strip(),
                    goal=goal.strip()
                )
                st.session_state.done = False
                st.rerun()
            except Exception as e:
                st.error(f"API 호출 오류: {e}")

# 과제용: 한계/고도화(필요하면 유지)
with st.expander("한계 및 고도화 방안(과제용)"):
    st.write("- **한계**: AI 제안이 항상 최적이라고 보장할 수 없고, 사용자 컨디션/과거 데이터 반영이 제한적입니다.")
    st.write("- **고도화**: 실행 기록을 축적해 성공률 높은 행동을 우선 추천하거나, 에너지 상태에 따라 5/10/15분 행동으로 조절할 수 있습니다.")
