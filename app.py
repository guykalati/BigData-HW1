"""
HW1 - Big Data SQL - Main Launcher
Run individual task apps using the sidebar.
"""
import streamlit as st
import os

st.set_page_config(page_title="HW1 - Big Data SQL", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #667eea, #764ba2, #f77062);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #333;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        transition: transform 0.2s;
    }
    .card:hover {
        transform: translateY(-5px);
        border-color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">📊 HW1 - Big Data & SQL</p>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#888; font-size:1.2rem;'>Interactive SQL applications built with Python, SQLite, and Streamlit</p>", unsafe_allow_html=True)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 👶 Task 1: Baby Names Explorer")
    st.markdown("Explore US baby name trends from 1880-2014 using SQLite. Features name popularity charts, custom SQL panel, and pattern discovery.")
    st.code("streamlit run task1_baby_names/app.py", language="bash")

    st.markdown("### ⚔️ Task 3: Pokémon Battle Arena")
    st.markdown("Battle Pokemon with stats-driven mechanics, type advantages, cheat codes that modify the database, and data insights.")
    st.code("streamlit run task3_pokemon/app.py", language="bash")

with col2:
    st.markdown("### 🏆 Task 2: Oscar Actor Explorer")
    st.markdown("Explore Oscar nominees and winners using SQLAlchemy ORM. Features actor profiles with Wikipedia integration.")
    st.code("streamlit run task2_oscar/app.py", language="bash")

    st.markdown("### 🕵️ Task 4: Detective SQL")
    st.markdown("A story-driven SQL learning game where you solve crimes by writing queries. 7 progressive levels with gamification.")
    st.code("streamlit run task4_sql_learning/app.py", language="bash")

st.divider()
st.markdown("""
### 🚀 How to Run
Each task is a standalone Streamlit app. Run them from the project root:
```bash
cd "/Users/gyklty/Desktop/Semester B/Big Data/HW1"
streamlit run task1_baby_names/app.py  # Baby Names
streamlit run task2_oscar/app.py       # Oscar Explorer
streamlit run task3_pokemon/app.py     # Pokemon Arena
streamlit run task4_sql_learning/app.py  # SQL Learning Game
```
""")
