import streamlit as st
import requests

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(page_title="🎬 나와 어울리는 영화는?", layout="centered")

TMDB_BASE_URL = "https://api.themoviedb.org/3"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"

GENRE_IDS = {
    "로맨스/드라마": [18, 10749],
    "액션/어드벤처": [28],
    "SF/판타지": [878, 14],
    "코미디": [35],
}

CHOICE_TO_GENRE = {
    "A": "로맨스/드라마",
    "B": "액션/어드벤처",
    "C": "SF/판타지",
    "D": "코미디",
}

PRIORITY = ["로맨스/드라마", "액션/어드벤처", "SF/판타지", "코미디"]

# -----------------------------
# 사이드바
# -----------------------------
st.sidebar.header("🔑 TMDB API 설정")
api_key = st.sidebar.text_input("TMDB API Key", type="password")

# -----------------------------
# UI
# -----------------------------
st.title("🎬 나와 어울리는 영화는?")
st.write("질문 5개로 당신의 영화 취향을 분석하고 추천해드려요!")

st.divider()

questions = [
    ("Q1. 시험이 끝난 금요일 밤, 당신의 선택은?", {
        "A": "조용히 대화하며 마무리",
        "B": "짜릿한 약속 잡기",
        "C": "혼자 콘텐츠 몰입",
        "D": "웃긴 영상 보기"
    }),
    ("Q2. 새 학기 OT에서 기대하는 순간은?", {
        "A": "깊은 대화",
        "B": "게임 리드",
        "C": "색다른 분위기",
        "D": "웃긴 상황"
    }),
    ("Q3. 스트레스 해소 방법은?", {
        "A": "음악·이야기 몰입",
        "B": "운동",
        "C": "게임·세계관",
        "D": "수다·웃음"
    }),
    ("Q4. 끌리는 주인공은?", {
        "A": "현실적인 성장형",
        "B": "리더형",
        "C": "특별한 능력",
        "D": "허술하지만 매력"
    }),
    ("Q5. 영화 후 만족 포인트는?", {
        "A": "여운",
        "B": "시원함",
        "C": "세계관",
        "D": "명대사"
    }),
]

answers = {}

for i, (q, opts) in enumerate(questions, start=1):
    choice = st.radio(q, [f"{k}. {v}" for k, v in opts.items()], key=f"q{i}")
    answers[f"q{i}"] = choice.split(".")[0]

st.divider()

# -----------------------------
# 분석 함수
# -----------------------------
def analyze(answers):
    score = {k: 0 for k in GENRE_IDS}
    evidence = {k: [] for k in GENRE_IDS}

    for idx, v in enumerate(answers.values(), start=1):
        genre = CHOICE_TO_GENRE[v]
        score[genre] += 1
        evidence[genre].append(idx)

    max_score = max(score.values())
    candidates = [k for k, v in score.items() if v == max_score]
    winner = next(g for g in PRIORITY if g in candidates)

    return winner, evidence

# -----------------------------
# TMDB 호출
# -----------------------------
def fetch_movies(api_key, genre_id):
    url = f"{TMDB_BASE_URL}/discover/movie"
    params = {
        "api_key": api_key,
        "with_genres": genre_id,
        "language": "ko-KR",
        "sort_by": "popularity.desc",
        "include_adult": False,
    }
    res = requests.get(url, params=params, timeout=10)
    return res.json().get("results", [])

# -----------------------------
# 결과
# -----------------------------
if st.button("결과 보기", type="primary"):
    if not api_key:
        st.error("TMDB API Key를 입력해주세요.")
        st.stop()

    with st.spinner("분석 중..."):
        genre, evidence = analyze(answers)
        genre_ids = GENRE_IDS[genre]

        movies = []
        seen = set()

        for gid in genre_ids:
            for m in fetch_movies(api_key, gid):
                if m["id"] not in seen and m.get("poster_path"):
                    movies.append(m)
                    seen.add(m["id"])
                if len(movies) >= 5:
                    break
            if len(movies) >= 5:
                break

    st.subheader("✅ 분석 결과")
    st.write(f"당신에게 어울리는 장르는 **{genre}** 입니다!")

    st.info(f"Q{', '.join(map(str, evidence[genre]))}에서 해당 성향이 두드러졌어요.")

    st.divider()
    st.subheader("🍿 추천 영화 TOP 5")

    for m in movies:
        cols = st.columns([1, 2])
        with cols[0]:
            st.image(POSTER_BASE_URL + m["poster_path"], use_container_width=True)
        with cols[1]:
            st.markdown(f"### {m['title']}")
            st.write(f"⭐ 평점: {m['vote_average']}")
            st.write(m["overview"] or "줄거리 정보 없음")
            st.caption(f"💡 {genre} 감성과 잘 맞는 인기 작품이에요.")
        st.divider()
