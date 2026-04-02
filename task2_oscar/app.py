"""
Task 2: Oscar Actor Explorer
Interactive Streamlit app using SQLAlchemy ORM for Oscar Awards data.
No raw SQL allowed — all queries go through the ORM.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import requests

from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, func, distinct
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.path.join(os.path.dirname(__file__), "oscar.db")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "the_oscar_award.csv")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)


# ============================================================
# ORM Models (Task 2.1)
# ============================================================
class OscarNomination(Base):
    """
    Each row = one nomination record.
    Schema design rationale:
    - Single table because each row in the CSV is one nomination event.
    - We store year_film and year_ceremony separately for accurate timeline queries.
    - 'winner' is stored as Boolean for easy filtering.
    - 'canon_category' normalizes category names across different years.
    """
    __tablename__ = 'nominations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    year_film = Column(Integer, nullable=False)
    year_ceremony = Column(Integer, nullable=False)
    ceremony = Column(Integer)
    category = Column(String, nullable=False)
    canon_category = Column(String)
    name = Column(String, nullable=False)
    film = Column(String)
    winner = Column(Boolean, default=False)


def init_db():
    """Load CSV into SQLite via ORM."""
    if os.path.exists(DB_PATH):
        return

    Base.metadata.create_all(engine)
    session = Session()

    df = pd.read_csv(DATA_PATH)
    records = []
    
    # Name normalization mapping to fix dataset inconsistencies
    corrections = {
        "Daniel Day Lewis": "Daniel Day-Lewis",
        "Donfeld": "Don Feld",
        "Mikkel E.G. Nielsen": "Mikkel E. G. Nielsen"
    }

    for _, row in df.iterrows():
        winner_val = str(row.get('winner', 'False')).strip().lower() in ['true', '1', 'yes']
        
        # Clean and normalize the name
        raw_name = str(row['name']) if pd.notna(row['name']) else 'Unknown'
        clean_name = " ".join(raw_name.strip().split())
        clean_name = corrections.get(clean_name, clean_name)

        # Filter out multi-person teams (which use '/') and studios/companies
        is_studio_or_team = any(x in clean_name.upper() for x in [
            "STUDIO", "CORPORATION", "CENTURY", "COMPANY", "DEPARTMENT", 
            "PRODUCTIONS", "PARAMOUNT", "UNIVERSAL", "WARNER", "ORCHESTRA",
            "MGM", "RKO", "WALT DISNEY", "COLUMBIA", "PIC.", "PICTURES"
        ])
        
        if "/" in clean_name or is_studio_or_team:
            continue

        records.append(OscarNomination(
            year_film=int(row['year_film']) if pd.notna(row['year_film']) else 0,
            year_ceremony=int(row['year_ceremony']) if pd.notna(row['year_ceremony']) else 0,
            ceremony=int(row['ceremony']) if pd.notna(row.get('ceremony', None)) else None,
            category=str(row['category']),
            canon_category=str(row.get('canon_category', row['category'])),
            name=clean_name,
            film=str(row['film']) if pd.notna(row['film']) else '',
            winner=winner_val
        ))

    session.bulk_save_objects(records)
    session.commit()
    session.close()


def get_wikipedia_info(name):
    """Fetch biography, birth date, and photo from Wikipedia REST API."""
    try:
        # Use Wikipedia REST API
        search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name.replace(' ', '_')}"
        headers = {'User-Agent': 'BigDataHW1/1.0 (student project)'}
        resp = requests.get(search_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            summary = data.get('extract', 'No summary available.')
            thumbnail = data.get('thumbnail', {}).get('source', None)
            description = data.get('description', '')
            return {
                'summary': summary,
                'thumbnail': thumbnail,
                'description': description,
            }
    except Exception as e:
        pass
    return {'summary': 'Could not fetch Wikipedia data.', 'thumbnail': None, 'description': ''}


# ============================================================
# Streamlit App
# ============================================================
st.set_page_config(page_title="Oscar Actor Explorer", page_icon="🏆", layout="wide")

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #FFD700, #FF8C00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    .profile-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #FFD700;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🏆 Oscar Actor Explorer</p>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#888'>Explore Academy Award nominees and winners since 1928</p>", unsafe_allow_html=True)

init_db()

tab = st.sidebar.radio("Navigate", [
    "🎭 Actor Profile",
    "🔍 Interesting Finds",
    "🎲 Did You Know?"
])

# ============================================================
# Task 2.2: Actor Profile App
# ============================================================
if tab == "🎭 Actor Profile":
    st.header("🎭 Actor/Director Profile Card")

    session = Session()
    # Get all unique names for autocomplete
    all_names = [r[0] for r in session.query(distinct(OscarNomination.name)).order_by(OscarNomination.name).all()]
    session.close()

    name_input = st.selectbox("Select or type an actor/director name:", options=[""] + all_names)

    if name_input:
        session = Session()

        # ORM queries — no raw SQL
        nominations = session.query(OscarNomination).filter(
            OscarNomination.name == name_input
        ).all()

        if not nominations:
            st.warning(f"No Oscar data found for '{name_input}'")
        else:
            wins = [n for n in nominations if n.winner]
            categories = list(set(n.canon_category for n in nominations))
            years = [n.year_ceremony for n in nominations]
            films_nominated = list(set(n.film for n in nominations if n.film))
            films_won = list(set(n.film for n in nominations if n.winner and n.film))

            # Wikipedia info
            wiki = get_wikipedia_info(name_input)

            # Display profile card
            col1, col2 = st.columns([1, 2])
            with col1:
                if wiki['thumbnail']:
                    st.image(wiki['thumbnail'], width=250)
                st.markdown(f"**{wiki['description']}**" if wiki['description'] else "")

            with col2:
                st.subheader(name_input)
                st.markdown(wiki['summary'])

            st.divider()

            # Stats
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Nominations", len(nominations))
            col2.metric("Wins", len(wins))
            win_rate = len(wins) / len(nominations) * 100 if nominations else 0
            col3.metric("Win Rate", f"{win_rate:.1f}%")
            col4.metric("Years Active", f"{min(years)}–{max(years)}")

            # Win gap analysis
            if wins:
                first_nom_year = min(years)
                first_win_year = min(n.year_ceremony for n in wins)
                gap = first_win_year - first_nom_year
                st.info(f"📅 Gap between first nomination and first win: **{gap} years** ({first_nom_year} → {first_win_year})")

            # Comparison to average
            avg_noms = session.query(func.count(OscarNomination.id)).group_by(OscarNomination.name).all()
            avg_nom_count = sum(x[0] for x in avg_noms) / len(avg_noms) if avg_noms else 0
            st.markdown(f"📊 Average nominee has **{avg_nom_count:.1f}** nominations. {name_input} has **{len(nominations)}**.")

            # Categories
            st.subheader("📂 Categories")
            for cat in categories:
                cat_noms = [n for n in nominations if n.canon_category == cat]
                cat_wins = [n for n in cat_noms if n.winner]
                st.markdown(f"- **{cat}**: {len(cat_noms)} nominations, {len(cat_wins)} wins")

            # Films
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🎬 Nominated Films")
                for f in sorted(films_nominated):
                    icon = "🏆" if f in films_won else "📋"
                    st.markdown(f"{icon} {f}")
            with col2:
                st.subheader("🏆 Winning Films")
                if films_won:
                    for f in sorted(films_won):
                        st.markdown(f"🏆 {f}")
                else:
                    st.markdown("_No wins yet_")

            # Timeline visualization
            st.subheader("📅 Oscar Timeline")
            timeline_data = []
            for n in nominations:
                timeline_data.append({
                    'Year': n.year_ceremony,
                    'Film': n.film,
                    'Category': n.canon_category,
                    'Result': '🏆 Won' if n.winner else '📋 Nominated',
                    'Winner': n.winner
                })
            timeline_df = pd.DataFrame(timeline_data)
            fig = px.scatter(timeline_df, x='Year', y='Category', color='Result',
                             hover_data=['Film'],
                             title=f"{name_input}'s Oscar Journey",
                             color_discrete_map={'🏆 Won': '#FFD700', '📋 Nominated': '#888'})
            fig.update_traces(marker=dict(size=15))
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        session.close()

# ============================================================
# Task 2.3: Interesting Finds
# ============================================================
elif tab == "🔍 Interesting Finds":
    st.header("🔍 Interesting Finds")

    session = Session()

    # Find 1: The Flawless Record (100% Win Rate with easiest multiple noms)
    st.subheader("1. The 'Flawless Record' (Never Lost)")
    flawless = session.query(
        OscarNomination.name,
        func.count(OscarNomination.id).label('noms')
    ).group_by(OscarNomination.name).having(
        func.cast(func.sum(func.cast(OscarNomination.winner, Integer)), Integer) == func.count(OscarNomination.id)
    ).having(
        func.count(OscarNomination.id) >= 3
    ).order_by(func.count(OscarNomination.id).desc()).limit(10).all()

    df1 = pd.DataFrame([(n.name, n.noms) for n in flawless], columns=['Name', 'Total Unbeaten Nominations'])
    fig1 = px.bar(df1, x='Name', y='Total Unbeaten Nominations',
                  title="People with 3+ Nominations and a 100% Win Rate 🏆",
                  color='Total Unbeaten Nominations', color_continuous_scale='Greens')
    fig1.update_layout(template="plotly_dark")
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown("""
    **Finding:** While getting nominated for an Oscar is hard, actually winning is even harder. But some rare 
    individuals have a **flawless record**—they have been nominated multiple times and have literally *never lost*. 
    These are artists whose work, whenever recognized by the Academy, was considered so undeniably the best of 
    the year that no one could beat them.
    """)

    # Find 2: The Versatile Visionaries (Most distinct categories)
    st.subheader("2. The Versatile Visionaries")
    versatile = session.query(
        OscarNomination.name,
        func.count(distinct(OscarNomination.canon_category)).label('cat_count'),
        func.count(OscarNomination.id).label('total_noms')
    ).group_by(OscarNomination.name).order_by(
        func.count(distinct(OscarNomination.canon_category)).desc()
    ).limit(10).all()

    df2 = pd.DataFrame([(n.name, n.cat_count, n.total_noms) for n in versatile], 
                       columns=['Name', 'Unique Categories', 'Total Nominations'])
    fig2 = px.scatter(df2, x='Total Nominations', y='Unique Categories', color='Name', 
                      size='Unique Categories', hover_name='Name',
                      title="Artists Nominated Across the Most Distinct Categories 🎭")
    fig2.update_traces(marker=dict(line=dict(width=2, color='white')))
    fig2.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("""
    **Finding:** Most actors or directors stay in their own lane, but a select few are true Renaissance people. 
    By grouping nominations by *distinct* categories, we uncover the most versatile artists in cinematic history—
    those who have been nominated for acting, directing, writing, and sometimes even producing or composing. 
    These individuals aren't just great at one job; they master the entire art of filmmaking.
    """)

    # Find 3: The "Double Threat" Phenomenon (Multiple Noms in One Year)
    st.subheader("3. The 'Double Threat' Phenomenon")
    subq = session.query(
        OscarNomination.name,
        OscarNomination.year_ceremony,
        func.count(OscarNomination.id).label('year_noms')
    ).group_by(OscarNomination.name, OscarNomination.year_ceremony).having(
        func.count(OscarNomination.id) > 1
    ).subquery()

    double_threats = session.query(
        subq.c.name,
        func.count(subq.c.year_ceremony).label('years_with_multiple_noms'),
        func.max(subq.c.year_noms).label('max_in_one_year')
    ).group_by(subq.c.name).order_by(
        func.count(subq.c.year_ceremony).desc(), 
        func.max(subq.c.year_noms).desc()
    ).limit(10).all()

    df3 = pd.DataFrame([(n.name, n.years_with_multiple_noms, n.max_in_one_year) for n in double_threats], 
                       columns=['Name', 'Years with 2+ Noms', 'Most Noms in a Single Year'])
    fig3 = px.bar(df3, x='Name', y='Years with 2+ Noms', hover_data=['Most Noms in a Single Year'], 
                  title="Artists Nominated Multiple Times in the EXACT Same Year 📆", 
                  color='Years with 2+ Noms', color_continuous_scale='Purples')
    fig3.update_layout(template="plotly_dark")
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown("""
    **Finding:** Getting nominated for an Oscar takes months of campaigning, but some people have managed to be 
    nominated *multiple times* in a single ceremony (e.g., Best Director + Best Original Screenplay, or Best 
    Actor + Best Supporting Actor). This chart shows the individuals who have pulled off this incredibly rare 
    "Double Threat" feat the most times in their careers.
    """)

    session.close()

# ============================================================
# Bonus: Did You Know?
# ============================================================
elif tab == "🎲 Did You Know?":
    st.header("🎲 Did You Know?")

    session = Session()

    all_names = [r[0] for r in session.query(distinct(OscarNomination.name)).order_by(OscarNomination.name).all()]

    if "dyk_name" not in st.session_state:
        st.session_state.dyk_name = "Meryl Streep" if "Meryl Streep" in all_names else all_names[0]

    def set_random_name():
        import random
        # Exclude names that are uninteresting (1 nomination) to make facts more fun
        multi_noms = session.query(OscarNomination.name).group_by(OscarNomination.name).having(func.count(OscarNomination.id) > 1).all()
        multi_list = [r[0] for r in multi_noms]
        st.session_state.dyk_name = random.choice(multi_list) if multi_list else random.choice(all_names)

    col1, col2 = st.columns([3, 1])
    with col1:
        # Autocomplete selectbox hooked into session_state!
        name_input = st.selectbox("Select an actor/director for a fun fact:", options=all_names, key="dyk_name")
    with col2:
        st.write("")
        st.write("")
        st.button("🎲 I'm Feeling Lucky", on_click=set_random_name, help="Randomly selects an interesting artist!")

    if name_input:
        # Count this person's nominations
        person_noms = session.query(func.count(OscarNomination.id)).filter(
            OscarNomination.name == name_input
        ).scalar()

        if person_noms == 0:
            st.warning(f"No Oscar data found for '{name_input}'")
        else:
            person_wins = session.query(func.count(OscarNomination.id)).filter(
                OscarNomination.name == name_input,
                OscarNomination.winner == True
            ).scalar()

            # Compare to all nominees
            all_nom_counts = session.query(
                func.count(OscarNomination.id)
            ).group_by(OscarNomination.name).all()
            all_counts = sorted([x[0] for x in all_nom_counts])
            percentile = sum(1 for x in all_counts if x <= person_noms) / len(all_counts) * 100

            # Get their categories
            categories = session.query(distinct(OscarNomination.canon_category)).filter(
                OscarNomination.name == name_input
            ).all()
            cat_list = [c[0] for c in categories]

            # First and last year
            first_year = session.query(func.min(OscarNomination.year_ceremony)).filter(
                OscarNomination.name == name_input
            ).scalar()
            last_year = session.query(func.max(OscarNomination.year_ceremony)).filter(
                OscarNomination.name == name_input
            ).scalar()
            span = last_year - first_year

            st.success(f"🌟 **Did You Know?** **{name_input}** has **{person_noms} nominations** — placing them in the top **{percentile:.0f}%** of all Oscar-nominated people in history!")
            
            # Formatted string logic
            win_text = f"They have won **{person_wins} time(s)**, with a win rate of **{person_wins/person_noms*100:.1f}%**" if person_wins > 0 else "They have yet to secure an Oscar win"
            st.markdown(f"🏆 {win_text}.")
            st.markdown(f"📂 They have been recognized in: **{', '.join(cat_list)}**")
            st.markdown(f"📅 Their Oscar career spans **{span} years** (from {first_year} to {last_year})")

    session.close()
