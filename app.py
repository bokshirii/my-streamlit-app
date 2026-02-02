import streamlit as st
import requests

st.set_page_config(page_title="나와 어울리는 영화는?", page_icon="🎬", layout="centered")

# -----------------------------
# TMDB 설정
# -----------------------------
TMDB_DISCOVER_URL = "https://api.themoviedb.org/3/discover/movie"
TMDB_POSTER_BASE = "https://image.tmdb.org/t/p/w500"

# 장르 ID (요구사항)
GENRE_IDS = {
    "액션/어드벤처": [28],          # 액션
    "코미디": [35],                # 코미디
    "로맨스/드라마": [18, 10749],  # 드라마 + 로맨스 (혼합 추천)
    "SF/판타지": [878, 14],        # SF + 판타지 (혼합 추천)
}

# 선택지(A/B/C/D) -> 성향 매핑
CHOICE_TO_TRAIT = {
    "A": "로맨스/드라마",
    "B": "액션/어드벤처",
    "C": "SF/판타지",
    "D": "코미디",
}

# -----------------------------
# 사이드바: API Key 입력
# -----------------------------
st.sidebar.header("🔑 TMDB 설정")
api_key = st.sidebar.text_input("TMDB API Key", type="password", placeholder="여기에 API Key 입력")

st.title("🎬 나와 어울리는 영화는?")
st.write("간단한 질문 5개로 당신의 영화 취향을 분석하고, TMDB에서 인기 영화 5개를 추천해드려요!")
st.caption("※ '결과 보기'를 누르면 선택한 답변을 바탕으로 장르를 결정하고 영화 추천을 가져옵니다.")

st.divider()

# -----------------------------
# 질문 데이터 (A/B/C/D 고정)
# -----------------------------
questions = [
    {
        "q": "Q1. 시험이 끝난 금요일 밤, 당신의 선택은?",
        "choices": {
            "A": "좋아하는 사람이나 친구와 조용히 대화하며 하루를 마무리한다",
            "B": "바로 약속 잡고 밖으로 나가 뭔가 짜릿한 걸 한다",
            "C": "혼자만의 시간, 상상력 자극하는 콘텐츠에 푹 빠진다",
            "D": "웃긴 영상이나 예능 보면서 아무 생각 없이 쉰다",
        },
    },
    {
        "q": "Q2. 새 학기 OT에서 당신이 가장 기대하는 순간은?",
        "choices": {
            "A": "새로운 사람들과 깊은 이야기를 나누게 되는 순간",
            "B": "레크리에이션이나 게임에서 팀을 이끌 때",
            "C": "독특한 사람들, 색다른 분위기를 발견할 때",
            "D": "예상치 못한 웃긴 상황이 터질 때",
        },
    },
    {
        "q": "Q3. 스트레스를 받을 때, 당신의 해소 방법은?",
        "choices": {
            "A": "감정이 잘 드러나는 음악이나 이야기에 몰입한다",
            "B": "운동하거나 몸을 쓰는 활동으로 확 풀어버린다",
            "C": "게임, 웹소설, 세계관 있는 콘텐츠에 빠진다",
            "D": "친구랑 수다 떨거나 웃긴 걸 보며 털어낸다",
        },
    },
    {
        "q": "Q4. 당신이 끌리는 주인공 유형은?",
        "choices": {
            "A": "현실적인 고민과 성장을 겪는 인물",
            "B": "위기 앞에서도 물러서지 않는 리더형 인물",
            "C": "특별한 능력이나 운명을 가진 인물",
            "D": "어딘가 허술하지만 정이 가는 인물",
        },
    },
    {
        "q": "Q5. 영화가 끝난 후, 가장 만족스러울 때는?",
        "choices": {
            "A": "여운이 남아서 한동안 생각이 이어질 때",
            "B": "“와, 진짜 시원하다”라는 말이 절로 나올 때",
            "C": "세계관이나 설정을 곱씹게 될 때",
            "D": "명장면보다 명대사가 먼저 떠오를 때",
        },
    },
]

# 세션 상태
if "answers" not in st.session_state:
    st.session_state["answers"] = {}  # q1..q5 -> "A"/"B"/"C"/"D"

# -----------------------------
# UI: 질문 표시 (st.radio)
# -----------------------------
for i, item in enumerate(questions, start=1):
    key = f"q{i}"
    options = [f"{k}. {v}" for k, v in item["choices"].items()]  # "A. ..."

    # 기본 선택값 지정(첫 옵션) + A/B/C/D 추출
    selected = st.radio(item["q"], options, key=key)
    st.session_state["answers"][key] = selected.split(".")[0].strip()  # "A"/"B"/"C"/"D"

    st.write("")

st.divider()

# -----------------------------
# 로직: 답변 분석 -> 장르 결정
# -----------------------------
def analyze_answers(answer_map: dict) -> dict:
    """
    return:
      {
        "scores": {trait: score},
        "winner": trait,
        "evidence": {trait: [q_indices]}
      }
    """
    scores = {trait: 0 for trait in GENRE_IDS.keys()}
    evidence = {trait: [] for trait in GENRE_IDS.keys()}

    for idx in range(1, 6):
        qk = f"q{idx}"
        choice = answer_map.get(qk)
        if choice in CHOICE_TO_TRAIT:
            trait = CHOICE_TO_TRAIT[choice]
            scores[trait] += 1
            evidence[trait].append(idx)

    # 동점 처리: 점수 높은 것들 중 "로맨스/드라마 -> 액션/어드벤처 -> SF/판타지 -> 코미디" 우선순위
    priority = ["로맨스/드라마", "액션/어드벤처", "SF/판타지", "코미디"]
    max_score = max(scores.values()) if scores else 0
    candidates = [t for t, s in scores.items() if s == max_score]
    winner = next((t for t in priority if t in candidates), candidates[0] if candidates else "로맨스/드라마")

    return {"scores": scores, "winner": winner, "evidence": evidence}

# -----------------------------
# TMDB: 영화 가져오기
# -----------------------------
def fetch_popular_movies(api_key: str, genre_id: int, limit: int = 5) -> list:
    """
    TMDB discover/movie에서 해당 장르의 인기 영화 목록을 가져옵니다.
    """
    params = {
        "api_key": api_key,
        "with_genres": str(genre_id),
        "language": "ko-KR",
        "sort_by": "popularity.desc",
        "include_adult": "false",
        "page": 1,
    }
    r = requests.get(TMDB_DISCOVER_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])
    return results[:limit]

def get_recommendations(api_key: str, trait: str, limit: int = 5) -> list:
    """
    trait에 매핑된 genre_id 목록을 순회하며 영화들을 모아,
    중복 제거 후 limit개 반환.
    """
    genre_ids = GENRE_IDS.get(trait, [])
    collected = []
    seen_ids = set()

    # 여러 장르(예: 드라마+로맨스, SF+판타지)는 섞어서 5개 채우기
    per_genre_limit = max(3, limit)  # 여유 있게 가져오고 중복 제거
    for gid in genre_ids:
        try:
            movies = fetch_popular_movies(api_key, gid, limit=per_genre_limit)
        except Exception:
            movies = []

        for m in movies:
            mid = m.get("id")
            if mid and mid not in seen_ids:
                seen_ids.add(mid)
                collected.append(m)
            if len(collected) >= limit:
                break
        if len(collected) >= limit:
            break

    return collected[:limit]

def build_reason(trait: str, evidence: dict) -> str:
    qs = evidence.get(trait, [])
    if not qs:
        return f"당신의 답변 흐름이 **{trait}** 성향과 잘 맞아요."

    q_list = ", ".join([f"Q{n}" for n in qs])
    if trait == "로맨스/드라마":
        return f"{q_list}에서 **감정/관계/여운**을 중시하는 선택이 많아서, **로맨스/드라마**가 잘 어울려요."
    if trait == "액션/어드벤처":
        return f"{q_list}에서 **활동적/도전/짜릿함**을 선호하는 선택이 많아서, **액션/어드벤처**가 잘 어울려요."
    if trait == "SF/판타지":
        return f"{q_list}에서 **상상력/세계관/비현실적 매력**을 선호하는 선택이 많아서, **SF/판타지**가 잘 어울려요."
    if trait == "코미디":
        return f"{q_list}에서 **가벼움/웃음/기분전환**을 선호하는 선택이 많아서, **코미디**가 잘 어울려요."
    return f"{q_list}의 선택을 보면 **{trait}** 성향이 뚜렷해요."

# -----------------------------
# 결과 보기 버튼
# -----------------------------
if st.button("결과 보기", type="primary"):
    if not api_key:
        st.error("사이드바에 TMDB API Key를 입력해 주세요.")
        st.stop()

    with st.spinner("분석 중..."):
        analysis = analyze_answers(st.session_state["answers"])
        winner = analysis["winner"]
        scores = analysis["scores"]
        evidence = analysis["evidence"]

        # 추천 영화 가져오기
        try:
            movies = get_recommendations(api_key, winner, limit=5)
        except requests.HTTPError as e:
            st.error(f"TMDB 요청에 실패했어요. API Key가 올바른지 확인해 주세요.\n\n에러: {e}")
            st.stop()
        except Exception as e:
            st.error(f"영화 추천을 가져오는 중 문제가 발생했어요.\n\n에러: {e}")
            st.stop()

    st.subheader("✅ 분석 결과")
    st.write(f"당신에게 가장 어울리는 장르는 **{winner}** 입니다!")

    # (선택) 점수 보여주기
    with st.expander("내 선택 성향 점수 보기"):
        st.write(scores)

    st.write("**이 장르를 추천하는 이유**")
    st.info(build_reason(winner, evidence))

    st.divider()
    st.subheader("🍿 추천 영화 TOP 5")

    if not movies:
        st.warning("추천할 영화를 찾지 못했어요. 잠시 후 다시 시도해 주세요.")
        st.stop()

    for m in movies:
        title = m.get("title") or m.get("name") or "제목 정보 없음"
        rating = m.get("vote_average")
        overview = m.get("overview") or "줄거리 정보가 없어요."
        poster_path = m.get("poster_path")

        cols = st.columns([1, 2])
        with cols[0]:
            if poster_path:
                st.image(f"{TMDB_POSTER_BASE}{poster_path}", use_container_width=True)
            else:
                st.caption("포스터 없음")

        with cols[1]:
            st.markdown(f"### {title}")
            if rating is not None:
                st.write(f"⭐ 평점: **{rating:.1f}** / 10")
            else:
                st.write("⭐ 평점: 정보 없음")
            st.write(overview)

            # 영화별 간단 추천 이유 (장르 기반으로 짧게)
            if winner == "로맨스/드라마":
                st.caption("💡 추천 이유: 감정선과 관계의 변화가 진하게 남는 작품이라 당신 취향에 잘 맞아요.")
            elif winner == "액션/어드벤처":
                st.caption("💡 추천 이유: 전개가 빠르고 액션의 쾌감이 확실한 작품이라 몰입하기 좋아요.")
            elif winner == "SF/판타지":
                st.caption("💡 추천 이유: 세계관/설정이 매력적이라 ‘상상하는 재미’를 제대로 채워줘요.")
            elif winner == "코미디":
                st.caption("💡 추천 이유: 부담 없이 웃으면서 볼 수 있어 기분전환용으로 딱이에요.")

        st.divider()
