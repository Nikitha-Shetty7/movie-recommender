 CineMatch — Movie Recommendation System

A Netflix-inspired movie recommendation web app built with Python and Streamlit.
It uses **content-based filtering** with TF-IDF and cosine similarity to recommend movies based on genres.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

 Demo

> Search any movie → get similar recommendations instantly!

**Try searching:** Toy Story, Batman, Inception, Matrix, Titanic

---

 Features

- 🔐 User Login & Registration with password hashing
- 🎯 Content-based movie recommendations
- 🎭 Browse movies by genre (Action, Comedy, Drama, Thriller, Romance, Horror)
- 🔍 Genre filter on search results
- 🖼️ Movie posters via OMDB API
- 🎨 Netflix-style dark UI

---

 Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Web app framework |
| Pandas | Data processing |
| scikit-learn | TF-IDF vectorizer & cosine similarity |
| Requests | API calls for movie posters |
| OMDB API | Fetching movie poster images |
| JSON + Hashlib | User authentication |

---

 Project Structure

```
movie-recommender/
├── app.py          # Main application file
├── movies.csv      # MovieLens movie dataset
├── links.csv       # IMDB/TMDB ID mappings
├── users.json      # Registered users (auto-created)
├── .gitignore      # Git ignore file
└── README.md       # Project documentation
```

---

## 🚀 How to Run Locally

**1. Clone the repository:**
```bash
git clone https://github.com/Nikitha-Shetty7/movie-recommender.git
cd movie-recommender
```

**2. Install dependencies:**
```bash
pip install pandas scikit-learn streamlit requests
```

**3. Run the app:**
```bash
streamlit run app.py
```

**4. Open in browser:**
```
http://localhost:8501
```

---

How It Works

1. Movies dataset is loaded from `movies.csv`
2. **TF-IDF Vectorizer** converts movie genres into numerical vectors
3. **Cosine Similarity** measures how similar two movies are
4. Top N most similar movies are returned as recommendations
5. Movie posters are fetched from OMDB API using IMDB IDs

---

 Dataset

Using the **MovieLens Dataset** from GroupLens:
- 27,000+ movies
- Genre-based content filtering
- Linked to IMDB IDs for poster fetching

---
 Authentication

- Passwords are hashed using **SHA-256** before storing
- User data stored locally in `users.json`
- Session management via Streamlit session state
---



---

## 👩‍💻 Author

**Nikitha Shetty**
GitHub: [@Nikitha-Shetty7](https://github.com/Nikitha-Shetty7)
