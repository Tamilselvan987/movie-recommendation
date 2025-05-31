import streamlit as st
import pandas as pd

st.set_page_config(page_title="🎬 MovieVerse", layout="wide")
st.title("🎬 MovieVerse:  Movie pedia")

@st.cache_data
def load_movies():
    return pd.read_pickle('movies_with_posters.pkl')

df = load_movies()

# Sidebar genre filter
all_genres = sorted(set(g for sublist in df['genres'] for g in sublist))
selected_genres = st.sidebar.multiselect("Filter by Genre", all_genres)

def get_recommendations_from_text(user_input):
    user_input = user_input.lower()

    stopwords = set([
        "recommend", "movie", "movies", "show", "some", "me", "please", "suggest", "can", "you",
        "anything", "about", "find", "like", "i", "want", "to", "give", "good",
        "interesting", "help", "tell", "list", "are", "on", "of", "for", "and", "the"
    ])

    words = [w.strip() for w in user_input.replace(',', ' ').split() if w not in stopwords and len(w) > 2]

    if not words:
        return pd.DataFrame(), "Please enter some keywords for movie recommendations."

    def contains_all_keywords(text):
        return all(kw in text for kw in words)

    genre_matches = df[df['genres'].apply(lambda genres: any(contains_all_keywords(genre.lower()) for genre in genres))]
    title_matches = df[df['original_title'].str.lower().apply(lambda t: contains_all_keywords(t))]
    overview_matches = df['overview'].fillna('').str.lower().apply(lambda o: contains_all_keywords(o))
    overview_matches = df[overview_matches]

    combined = pd.concat([genre_matches, title_matches, overview_matches]).drop_duplicates(subset='original_title')

    if not combined.empty:
        return combined, f"Found {len(combined)} great matches based on your input! 🎥"
    else:
        return pd.DataFrame(), "Sorry, no recommendations found. Try another title, genre, or keyword."

def simple_chatbot(user_input):
    user_input = user_input.lower()
    if any(g.lower() in user_input for g in all_genres) or "recommend" in user_input or "movie" in user_input or "movies" in user_input:
        matched_movies, response = get_recommendations_from_text(user_input)
        return matched_movies, response
    elif "hello" in user_input or "hi" in user_input:
        return pd.DataFrame(), "Hello! Ask me anything about movies."
    elif "bye" in user_input or "thank" in user_input:
        return pd.DataFrame(), "You're welcome! Enjoy your movies! 🍿"
    else:
        return pd.DataFrame(), "Sorry, I can only help with movie recommendations. Try searching or filtering movies!"

st.sidebar.markdown("## Chatbot 🎤")
chat_input = st.sidebar.text_input("Ask me anything about movies!")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if chat_input:
    matched_movies, response = simple_chatbot(chat_input)
    st.session_state.chat_history.append((chat_input, response, matched_movies))
    st.session_state.page = 0  # reset page on new query

if st.session_state.chat_history:
    with st.sidebar.expander("Chatbot response", expanded=True):
        for q, a, _ in st.session_state.chat_history:
            st.markdown(f"**You:** {q}")
            st.markdown(f"**Bot:** {a}")
            st.markdown("---")

search_term = st.text_input("Search movies by title:")

# Filter by genres
if selected_genres:
    filtered_df = df[df['genres'].apply(lambda genres: any(g in genres for g in selected_genres))]
else:
    filtered_df = df.copy()

# Filter by search term
if search_term:
    filtered_df = filtered_df[filtered_df['original_title'].str.contains(search_term, case=False, na=False)]

# Use chatbot result if available
if st.session_state.chat_history and st.session_state.chat_history[-1][2] is not None and not st.session_state.chat_history[-1][2].empty:
    display_df = st.session_state.chat_history[-1][2]
else:
    display_df = filtered_df

# Reset page if search or filter is used
st.session_state.page = st.session_state.get("page", 0)
total_movies = len(display_df)
MOVIES_PER_PAGE = 8
total_pages = (total_movies - 1) // MOVIES_PER_PAGE + 1

# Pagination controls
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("⬅️ Previous") and st.session_state.page > 0:
        st.session_state.page -= 1
with col3:
    if st.button("Next ➡️") and st.session_state.page < total_pages - 1:
        st.session_state.page += 1

start_idx = st.session_state.page * MOVIES_PER_PAGE
end_idx = start_idx + MOVIES_PER_PAGE
st.markdown(f"### Showing movies {start_idx + 1} to {min(end_idx, total_movies)} of {total_movies}")

def show_movies(movies_df):
    if movies_df.empty:
        st.write("No movies found.")
        return
    for i in range(0, len(movies_df), 4):
        cols = st.columns(4)
        for idx, (_, row) in enumerate(movies_df.iloc[i:i+4].iterrows()):
            with cols[idx]:
                st.subheader(row['original_title'])
                poster_url = row.get('poster_url', None)
                if poster_url:
                    st.image(poster_url, use_column_width=True)
                genres_str = ", ".join(row['genres']) if isinstance(row['genres'], list) else "N/A"
                st.write(f"**Genres:** {genres_str}")
                overview = row.get('overview', '')
                if isinstance(overview, str) and overview:
                    st.write(overview[:150] + ("..." if len(overview) > 150 else ""))
                st.markdown("---")

# Show movies for current page
show_movies(display_df.iloc[start_idx:end_idx])





