import streamlit as st
import tmdbsimple as tmdb

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(page_title="나와 어울리는 영화는?", page_icon="🎬", layout="centered")
TMDB_POSTER_BASE = "https://image.tmdb.org/t/p/w500"

# 장르 ID (요구사항)
GENRE_IDS = {
    "액션/어드벤처": [28],          # 액션
    "코미디": [35],                # 코미디
    "로맨스/드라마": [18, 10749],  # 드라마 + 로맨스
    "SF/판타지": [878, 14],        # SF + 판타지
}

# A/B/C/D -> 성향
CHOICE_TO_TRAIT = {
    "A": "로맨스/드라마",
    "B": "액션/어드벤처",
    "C": "SF/판타지",
    "D": "코미디",
}

# 동점 우선순위
TRAIT_PRIORITY = ["로맨스/드라마", "액션/어드벤처", "SF/판타지", "코미디"]

# -----------------------------
# 사이드바
# -----------------------------
st.sidebar.header("🔑 TMDB 설정")
api_key = st.sidebar.text_input("TMDB API Key", type="password", placeholder="여기에 API Key 입력")

region = st.sidebar.selectbox("Region (선택)", ["KR", "US", "JP", "GB", "FR", "DE"], index=0)
prefer_language = st.sidebar.selectbox("언어", ["ko-KR", "en-US"], index=0)
show_trailer = st.sidebar.toggle("트레일러 링크 표시", value=True)

st.sidebar.caption("팁: API Key가 없으면 TMDB 개발자 사이트에서 발급받아 입력하세요.")

# -----------------------------
# UI
# -----------------------------
st.title("🎬 나와 어울리는 영화는?")
st.write("질문 5개로 당신의 영화 취향을 분석하고, TMDB에서 인기 영화 5개를 추천해드려요!")
st.caption("※ 결과 보기 버튼을 누르면 장르를 결정하고 추천 영화를 가져옵니다.")

st.divider()

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

if "answers" not in st.session_state:
    st.session_state["answers"] = {}  # q1..q5 -> "A"/"B"/"C"/"D"

# 질문 표시
for i, item in enumerate(questions, start=1):
    key = f"q{i}"
    options = [f"{k}. {v}" for k, v in item["choices"].items()]
    selected = st.radio(item["q"], options, key=key)
    st.session_state["answers"][key] = selected.split(".")[0].strip()
    st.write("")

st.divider()

# -----------------------------
# 분석 로직
# -----------------------------
def analyze_answers(answer_map: dict) -> dict:
    scores = {trait: 0 for trait in GENRE_IDS.keys()}
    evidence = {trait: [] for trait in GENRE_IDS.keys()}

    for idx in range(1, 6):
        qk = f"q{idx}"
        choice = answer_map.get(qk)
        trait = CHOICE_TO_TRAIT.get(choice)
        if trait:
            scores[trait] += 1
            evidence[trait].append(idx)

    max_score = max(scores.values()) if scores else 0
    candidates = [t for t, s in scores.items() if s == max_score]
    winner = next((t for t in TRAIT_PRIORITY if t in candidates), candidates[0] if candidates else "로맨스/드라마")

    return {"scores": scores, "winner": winner, "evidence": evidence}

def build_trait_reason(trait: str, evidence: dict) -> str:
    qs = evidence.get(trait, [])
    q_list = ", ".join([f"Q{n}" for n in qs]) if qs else ""

    if trait == "로맨스/드라마":
        return f"{q_list}에서 **감정/관계/여운**을 중시하는 선택이 많아 **로맨스/드라마**가 잘 어울려요."
    if trait == "액션/어드벤처":
        return f"{q_list}에서 **활동/도전/짜릿함**을 선호하는 흐름이 보여 **액션/어드벤처**가 딱이에요."
    if trait == "SF/판타지":
        return f"{q_list}에서 **상상력/세계관/비현실적 매력**을 선호해서 **SF/판타지** 취향에 가깝습니다."
    if trait == "코미디":
        return f"{q_list}에서 **가벼움/웃음/기분전환**을 중시하는 선택이 많아 **코미디**가 어울려요."
    return f"당신의 답변 흐름이 **{trait}** 성향과 잘 맞아요."

# -----------------------------
# TMDB 호출 (tmdbsimple + 캐싱)
# -----------------------------
@st.cache_data(ttl=60 * 30)
def tmdb_discover_movies(api_key: str, genre_id: int, language: str, region: str, page: int = 1) -> list:
    tmdb.API_KEY = api_key
    discover = tmdb.Discover()
    # tmdbsimple은 kwargs를 그대로 쿼리 파라미터로 넘겨줍니다.
    data = discover.movie(
        with_genres=str(genre_id),
        language=language,
        region=region,
        sort_by="popularity.desc",
        include_adult=False,
        page=page,
    )
    return (data or {}).get("results", []) or []

@st.cache_data(ttl=60 * 60)
def tmdb_movie_details(api_key: str, movie_id: int, language: str):
    tmdb.API_KEY = api_key
    # append_to_response로 credits/videos 같이 받기
    movie = tmdb.Movies(movie_id)
    return movie.info(language=language, append_to_response="credits,videos")

def pick_movies(api_key: str, trait: str, language: str, region: str, limit: int = 5) -> list:
    genre_ids = GENRE_IDS.get(trait, [])
    seen = set()
    picked = []

    # 여러 장르 섞기 + 페이지를 넘기며 5개 채우기
    # (포스터 없는 영화는 제외)
    max_pages = 5

    for gid in genre_ids:
        for page in range(1, max_pages + 1):
            results = tmdb_discover_movies(api_key, gid, language, region, page=page)
            if not results:
                break

            for m in results:
                mid = m.get("id")
                if not mid or mid in seen:
                    continue
                if not m.get("poster_path"):  # 포스터 없으면 제외(화면 품질)
                    continue

                seen.add(mid)
                picked.append(m)
                if len(picked) >= limit:
                    return picked

    return picked[:limit]

def ensure_korean_fallback(text_ko: str, text_en: str) -> str:
    # ko-KR 데이터가 비어있으면 en-US로 폴백
    if text_ko and text_ko.strip():
        return text_ko
    return text_en or ""

def build_movie_reason(trait: str, details: dict) -> str:
    genres = [g.get("name") for g in (details.get("genres") or []) if g.get("name")]
    top_genres = ", ".join(genres[:2]) if genres else ""

    credits = details.get("credits") or {}
    cast = credits.get("cast") or []
    top_cast = ", ".join([c.get("name") for c in cast[:3] if c.get("name")])

    # 성향별 한 줄 이유(장르/출연진을 살짝 곁들임)
    if trait == "로맨스/드라마":
        base = "감정선과 관계의 변화에 집중할 수 있는 작품이라 취향에 잘 맞아요."
    elif trait == "액션/어드벤처":
        base = "전개가 빠르고 긴장감 있는 장면이 많아 몰입하기 좋아요."
    elif trait == "SF/판타지":
        base = "설정/세계관이 강해서 ‘상상하는 재미’를 제대로 채워줘요."
    else:
        base = "부담 없이 웃으면서 볼 수 있어 기분전환용으로 좋아요."

    extra = []
    if top_genres:
        extra.append(f"장르: {top_genres}")
    if top_cast:
        extra.append(f"출연: {top_cast}")

    return base + (f" ({' · '.join(extra)})" if extra else "")

def extract_trailer_link(details: dict) -> str | None:
    videos = (details.get("videos") or {}).get("results") or []
    # 유튜브 트레일러 우선
    for v in videos:
        if v.get("site") == "YouTube" and (v.get("type") in ["Trailer", "Teaser"]):
            key = v.get("key")
            if key:
                return f"https://www.youtube.com/watch?v={key}"
    return None

# -----------------------------
# 결과 보기
# -----------------------------
if st.button("결과 보기", type="primary"):
    if not api_key:
        st.error("사이드바에 TMDB API Key를 입력해 주세요.")
        st.stop()

    analysis = analyze_answers(st.session_state["answers"])
    winner = analysis["winner"]
    scores = analysis["scores"]
    evidence = analysis["evidence"]

    with st.spinner("분석 중..."):
        # 1) 먼저 선호 언어로 추천 후보를 가져오고
        movies = pick_movies(api_key, winner, prefer_language, region, limit=5)

        # 2) 부족하면 영어로 한 번 더 채워보기(폴백)
        if len(movies) < 5 and prefer_language != "en-US":
            more = pick_movies(api_key, winner, "en-US", region, limit=5)
            # 중복 제거해서 추가
            existing_ids = {m.get("id") for m in movies}
            for m in more:
                if m.get("id") not in existing_ids:
                    movies.append(m)
                    existing_ids.add(m.get("id"))
                if len(movies) >= 5:
                    break
            movies = movies[:5]

    st.subheader("✅ 분석 결과")
    st.write(f"당신에게 가장 어울리는 장르는 **{winner}** 입니다!")

    with st.expander("내 선택 성향 점수 보기"):
        st.write(scores)

    st.write("**이 장르를 추천하는 이유**")
    st.info(build_trait_reason(winner, evidence))

    st.divider()
    st.subheader("🍿 추천 영화 TOP 5")

    if not movies:
        st.warning("추천할 영화를 찾지 못했어요. 잠시 후 다시 시도해 주세요.")
        st.stop()

    for m in movies:
        mid = m.get("id")
        poster_path = m.get("poster_path")

        # 카드 기본 정보(리스트에서 제공되는 값)
        title_list = m.get("title") or "제목 정보 없음"
        rating = m.get("vote_average")
        overview_list = m.get("overview") or ""

        # 상세 정보(append_to_response)
        details = {}
        try:
            details = tmdb_movie_details(api_key, int(mid), prefer_language)
        except Exception:
            details = {}

        # ko 비어있으면 en으로 폴백(상세 한 번 더)
        if prefer_language == "ko-KR":
            try:
                details_en = tmdb_movie_details(api_key, int(mid), "en-US")
            except Exception:
                details_en = {}
        else:
            details_en = {}

        title = ensure_korean_fallback(details.get("title") or title_list, details_en.get("title"))
        overview = ensure_korean_fallback(details.get("overview") or overview_list, details_en.get("overview"))

        trailer = extract_trailer_link(details) if show_trailer else None

        cols = st.columns([1, 2])
        with cols[0]:
            if poster_path:
                st.image(f"{TMDB_POSTER_BASE}{poster_path}", use_container_width=True)
            else:
                st.caption("포스터 없음")

        with cols[1]:
            st.markdown(f"### {title}")
            if rating is not None:
                st.write(f"⭐ 평점: **{float(rating):.1f}** / 10")
            else:
                st.write("⭐ 평점: 정보 없음")

            st.write(overview if overview else "줄거리 정보가 없어요.")

            st.caption("💡 이 영화를 추천하는 이유: " + build_movie_reason(winner, details))

            if trailer:
                st.link_button("▶️ 트레일러 보기", trailer)

        st.divider()
