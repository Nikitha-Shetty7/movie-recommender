import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st
import requests
import json
import os
import hashlib

# ─── CONFIG ───────────────────────────────────────────────────────────────────
OMDB_API_KEY = "thewdb"   # Free demo key - works without Patreon
USERS_FILE = "users.json"

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CineMatch",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    html, body, [class*="css"] {
        background-color: #141414;
        color: #ffffff;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .stApp { background-color: #141414; }
    #MainMenu, footer, header {visibility: hidden;}
    .big-title {
        font-size: 3rem;
        font-weight: 900;
        color: #E50914;
        text-align: center;
        margin-bottom: 0.2rem;
        letter-spacing: 2px;
    }
    .subtitle {
        text-align: center;
        color: #aaaaaa;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .stTextInput > div > div > input {
        background-color: #333333;
        color: white;
        border: 1px solid #555;
        border-radius: 4px;
        padding: 10px;
        font-size: 1rem;
    }
    .stTextInput > div > div > input:focus {
        border-color: #E50914;
        box-shadow: 0 0 0 2px rgba(229,9,20,0.3);
    }
    .stButton > button {
        background-color: #E50914;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 10px 24px;
        font-size: 1rem;
        font-weight: bold;
        width: 100%;
        cursor: pointer;
        transition: background 0.2s;
    }
    .stButton > button:hover {
        background-color: #f40612;
        transform: scale(1.02);
    }
    .movie-card {
        background-color: #1f1f1f;
        border-radius: 8px;
        overflow: hidden;
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer;
        margin-bottom: 16px;
        width: 100%;
        min-height: 320px;
    }
    .movie-card:hover {
        transform: scale(1.03);
        box-shadow: 0 8px 30px rgba(229,9,20,0.4);
    }
    .movie-card img {
        width: 100%;
        height: 260px;
        object-fit: cover;
        border-radius: 8px 8px 0 0;
        display: block;
    }
    .movie-info { padding: 10px; }
    .movie-title {
        font-size: 0.85rem;
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        line-height: 1.3;
    }
    .movie-genre {
        font-size: 0.72rem;
        color: #aaaaaa;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ffffff;
        margin: 1.5rem 0 1rem 0;
        border-left: 4px solid #E50914;
        padding-left: 12px;
    }
    .stSelectbox > div > div {
        background-color: #333333;
        color: white;
        border: 1px solid #555;
        border-radius: 4px;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1f1f1f;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #aaaaaa;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        color: #E50914;
        border-bottom: 2px solid #E50914;
    }
    hr { border-color: #333333; }
</style>
""", unsafe_allow_html=True)


# ─── USER AUTH ────────────────────────────────────────────────────────────────
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def register_user(username, password):
    users = load_users()
    if username in users:
        return False, "Username already exists!"
    users[username] = hash_password(password)
    save_users(users)
    return True, "Account created successfully!"

def login_user(username, password):
    users = load_users()
    if username not in users:
        return False, "Username not found!"
    if users[username] != hash_password(password):
        return False, "Incorrect password!"
    return True, "Login successful!"


# ─── MOVIE DATA ───────────────────────────────────────────────────────────────
@st.cache_data
def load_movies():
    # Load movies - tab separated
    movies = pd.read_csv("movies.csv", sep='\t', engine='python', on_bad_lines='skip')
    movies.columns = movies.columns.str.strip().str.lower()

    if "genre" in movies.columns:
        movies = movies.rename(columns={"genre": "genres"})

    movies["genres"] = movies["genres"].str.replace("|", " ", regex=False)

    # Load links - tab separated, keep imdbId for OMDB
    try:
        links = pd.read_csv("links.csv", sep='\t', engine='python', on_bad_lines='skip')
        links.columns = links.columns.str.strip().str.lower()
        movies = movies.merge(links[["movieid", "imdbid"]], on="movieid", how="left")
        movies = movies.rename(columns={"movieid": "movieId", "imdbid": "imdbId"})
    except Exception as e:
        movies["imdbId"] = None

    return movies


@st.cache_data
def build_similarity():
    movies = load_movies()
    tfidf = TfidfVectorizer(stop_words="english")
    tfidf_matrix = tfidf.fit_transform(movies["genres"])
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    return cosine_sim


@st.cache_data
def get_poster_by_imdb(imdb_id):
    try:
        if imdb_id and not pd.isna(imdb_id):
            imdb_formatted = f"tt{int(imdb_id):07d}"
            url = f"http://www.omdbapi.com/?i={imdb_formatted}&apikey={OMDB_API_KEY}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, timeout=8, headers=headers)
            data = response.json()
            poster = data.get("Poster")
            if poster and poster != "N/A":
                return poster
    except:
        pass
    return "https://placehold.co/300x450/1f1f1f/E50914?text=No+Poster"


def recommend(movie_title, num=12):
    movies = load_movies()
    cosine_sim = build_similarity()
    movies["title_lower"] = movies["title"].str.lower()
    matches = movies[movies["title_lower"].str.contains(movie_title.lower(), na=False)]
    if matches.empty:
        return []
    idx = matches.index[0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:num+1]
    movie_indices = [i[0] for i in sim_scores]
    return movies[["title", "genres", "imdbId"]].iloc[movie_indices].values.tolist()


# ─── LOGIN PAGE ───────────────────────────────────────────────────────────────
def show_login_page():
    st.markdown('<div class="big-title">🎬 CineMatch</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Your Personal Movie Recommendation Engine</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab1, tab2 = st.tabs(["  Sign In  ", "  Register  "])

        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            username = st.text_input("Username", key="login_user", placeholder="Enter username")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Sign In", key="signin_btn"):
                if username and password:
                    success, msg = login_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill in all fields.")

        with tab2:
            st.markdown("<br>", unsafe_allow_html=True)
            new_user = st.text_input("Choose Username", key="reg_user", placeholder="Enter username")
            new_pass = st.text_input("Choose Password", type="password", key="reg_pass", placeholder="Enter password")
            confirm_pass = st.text_input("Confirm Password", type="password", key="reg_confirm", placeholder="Confirm password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Create Account", key="register_btn"):
                if new_user and new_pass and confirm_pass:
                    if new_pass != confirm_pass:
                        st.error("Passwords do not match!")
                    elif len(new_pass) < 6:
                        st.error("Password must be at least 6 characters!")
                    else:
                        success, msg = register_user(new_user, new_pass)
                        if success:
                            st.success(msg + " Please sign in.")
                        else:
                            st.error(msg)
                else:
                    st.warning("Please fill in all fields.")


# ─── MAIN APP ─────────────────────────────────────────────────────────────────
def show_main_app():
    col1, col2, col3 = st.columns([2, 6, 2])
    with col1:
        st.markdown('<span style="color:#E50914;font-size:1.8rem;font-weight:900;">🎬 CineMatch</span>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div style="text-align:right;color:#aaa;padding-top:8px;">👤 {st.session_state.username}</div>', unsafe_allow_html=True)
        if st.button("Sign Out", key="signout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

    st.markdown("---")

    st.markdown('<div class="section-header">🔍 Find Your Movie</div>', unsafe_allow_html=True)
    col_search, col_btn = st.columns([4, 1])
    with col_search:
        movie_input = st.text_input("Search Movie", placeholder="Search a movie e.g. Toy Story, Batman, Inception...", label_visibility="collapsed")
    with col_btn:
        search_clicked = st.button("🎬 Recommend", key="recommend_btn")

    movies = load_movies()
    all_genres = sorted(set(
        genre for genres in movies["genres"].dropna().str.split()
        for genre in genres if genre != "(no"
    ))
    selected_genre = st.selectbox("Filter by Genre (optional)", ["All Genres"] + all_genres)

    if search_clicked and movie_input:
        results = recommend(movie_input, num=12)

        if results:
            if selected_genre != "All Genres":
                results = [r for r in results if selected_genre.lower() in r[1].lower()]

            if results:
                st.markdown(f'<div class="section-header">🎯 Because you searched: <span style="color:#E50914">{movie_input}</span></div>', unsafe_allow_html=True)
                cols = st.columns(4, gap="medium")
                for i, (title, genres, imdb_id) in enumerate(results):
                    with cols[i % 4]:
                        poster_url = get_poster_by_imdb(imdb_id)
                        clean_genres = genres.replace(" ", " · ")
                        st.markdown(f"""
                        <div class="movie-card">
                            <img src="{poster_url}" alt="{title}" onerror="this.src='https://placehold.co/300x450/1f1f1f/E50914?text=No+Poster'"/>
                            <div class="movie-info">
                                <div class="movie-title">{title}</div>
                                <div class="movie-genre">{clean_genres[:40]}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning(f"No {selected_genre} movies found similar to '{movie_input}'.")
        else:
            st.error(f"Movie '{movie_input}' not found! Try: Toy Story, Batman, Inception")

    elif search_clicked and not movie_input:
        st.warning("Please enter a movie name.")

    st.markdown('<div class="section-header">🎭 Browse by Genre</div>', unsafe_allow_html=True)
    genre_cols = st.columns(6)
    popular_genres = ["Action", "Comedy", "Drama", "Thriller", "Romance", "Horror"]
    for i, genre in enumerate(popular_genres):
        with genre_cols[i]:
            if st.button(genre, key=f"genre_{genre}"):
                genre_movies = movies[movies["genres"].str.contains(genre, na=False)].head(8)
                st.markdown(f'<div class="section-header">🎬 Top {genre} Movies</div>', unsafe_allow_html=True)
                gcols = st.columns(4, gap="medium")
                for j, (_, row) in enumerate(genre_movies.iterrows()):
                    with gcols[j % 4]:
                        poster_url = get_poster_by_imdb(row.get("imdbId"))
                        st.markdown(f"""
                        <div class="movie-card">
                            <img src="{poster_url}" alt="{row['title']}" onerror="this.src='https://placehold.co/300x450/1f1f1f/E50914?text=No+Poster'"/>
                            <div class="movie-info">
                                <div class="movie-title">{row['title']}</div>
                                <div class="movie-genre">{row['genres'][:40]}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

if st.session_state.logged_in:
    show_main_app()
else:
    show_login_page()