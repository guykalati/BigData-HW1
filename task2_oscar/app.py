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
    # Fetch all data to process safely in Python, completely avoiding SQLite anomalies
    all_noms = session.query(OscarNomination).all()
    session.close()

    # Robust filter to guarantee no studios/military/teams are included
    ignore_words = [
        'NAVY', 'ARMY', 'STUDIO', 'CORPORATION', 'FOX', 'MGM', 'METRO-GOLDWYN', 'METRO GOLDWYN', 'WARNER',
        'PARAMOUNT', 'DISNEY', '/', 'DEPARTMENT', 'PRODUCTIONS', 'ORCHESTRA', 'COMPANY', 'COLUMBIA', 'PICTURES'
    ]

    # Pre-process stats per person
    stats = {}
    categories_per_person = {}
    years_per_person = {}
    
    for n in all_noms:
        if any(w in n.name.upper() for w in ignore_words):
            continue
            
        name = n.name
        if name not in stats:
            stats[name] = {'noms': 0, 'wins': 0}
            categories_per_person[name] = set()
            years_per_person[name] = []
            
        stats[name]['noms'] += 1
        if n.winner:
            stats[name]['wins'] += 1
            
        categories_per_person[name].add(n.canon_category)
        years_per_person[name].append(n.year_ceremony)

    # Find 1: The Flawless Record 
    st.subheader("1. The 'Flawless Record' (Never Lost)")
    flawless = [
        {'Name': name, 'Unbeaten Nominations': data['wins']} 
        for name, data in stats.items() 
        if data['wins'] == data['noms'] and data['noms'] >= 3
    ]
    flawless = sorted(flawless, key=lambda x: x['Unbeaten Nominations'], reverse=True)[:10]

    df1 = pd.DataFrame(flawless)
    fig1 = px.bar(df1, x='Name', y='Unbeaten Nominations',
                  title="People with 3+ Nominations and a Flawless 100% Win Rate 🏆",
                  color='Unbeaten Nominations', color_continuous_scale='Greens')
    fig1.update_layout(template="plotly_dark")
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown("""
    **Finding:** Some rare individuals have a **flawless record**—they have been nominated multiple times 
    and have literally *never lost*. These are artists whose work was considered so undeniably the best of 
    the year that no opponent could beat them.
    """)

    # Find 2: The Versatile Visionaries 
    st.subheader("2. The Versatile Visionaries")
    versatile = [
        {'Name': name, 'Unique Categories': len(cats), 'List': ", ".join(sorted(cats))}
        for name, cats in categories_per_person.items()
    ]
    versatile = sorted(versatile, key=lambda x: x['Unique Categories'], reverse=True)[:10]
    
    df2 = pd.DataFrame(versatile)
    # Improved Representation: Horizontal bar chart
    fig2 = px.bar(df2, x='Unique Categories', y='Name', orientation='h', 
                  text='Unique Categories', hover_data=['List'],
                  title="Artists Nominated Across the Most Distinct Categories 🎭",
                  color='Unique Categories', color_continuous_scale='Sunset')
    fig2.update_traces(textposition='inside')
    fig2.update_layout(yaxis={'categoryorder':'total ascending'}, template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("""
    **Finding:** Most artists specialize, but a select few are true Renaissance people. By grouping 
    nominations by *distinct* categories, we uncover the most versatile artists in cinematic history—
    those who master the entire art of filmmaking (acting, directing, writing, producing).
    """)

    # Find 3: The Longevity Legends (Career Span)
    st.subheader("3. The 'Longevity Legends' (Longest Oscar Spans)")
    longevity = []
    for name, yrs in years_per_person.items():
        if len(yrs) >= 2:
            span = max(yrs) - min(yrs)
            longevity.append({'Name': name, 'Span in Years': span, 'First Nom': min(yrs), 'Last Nom': max(yrs)})
            
    longevity = sorted(longevity, key=lambda x: x['Span in Years'], reverse=True)[:10]
    df3 = pd.DataFrame(longevity)
    
    fig3 = px.bar(df3, x='Span in Years', y='Name', orientation='h',
                  hover_data=['First Nom', 'Last Nom'], 
                  title="Artists with the Longest Gap Between First and Last Nomination ⏳",
                  color='Span in Years', color_continuous_scale='Teal')
    fig3.update_layout(yaxis={'categoryorder':'total ascending'}, template="plotly_dark")
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown("""
    **Finding:** In Hollywood, it's easy to be a flash in the pan. The hardest thing to do is maintain 
    relevance across generations. These are the artists who hold the record for the absolute longest 
    career spans, navigating decades of shifting industry trends while remaining consistently Academy-worthy!
    """)


# ============================================================
# Bonus: Did You Know?
# ============================================================
elif tab == "🎲 Did You Know?":
    st.header("🎲 Did You Know?")

    session = Session()

    # Filter out studios natively for the dropdown list too
    ignore_words = [
        'NAVY', 'ARMY', 'STUDIO', 'CORPORATION', 'FOX', 'MGM', 'METRO', 'WARNER',
        'PARAMOUNT', 'DISNEY', '/', 'DEPARTMENT', 'PRODUCTIONS', 'ORCHESTRA'
    ]
    
    raw_names = [r[0] for r in session.query(distinct(OscarNomination.name)).all()]
    all_names = sorted([n for n in raw_names if not any(w in n.upper() for w in ignore_words)])

    if "dyk_name" not in st.session_state:
        st.session_state.dyk_name = "Meryl Streep" if "Meryl Streep" in all_names else all_names[0]

    def set_random_name():
        import random
        multi_noms = session.query(OscarNomination.name).group_by(OscarNomination.name).having(func.count(OscarNomination.id) > 1).all()
        multi_list = sorted([r[0] for r in multi_noms if not any(w in r[0].upper() for w in ignore_words)])
        st.session_state.dyk_name = random.choice(multi_list) if multi_list else random.choice(all_names)

    col1, col2 = st.columns([3, 1])
    with col1:
        # User input bound to session state
        name_input = st.selectbox("Select an actor/director for a fun fact:", options=all_names, key="dyk_name")
    with col2:
        st.write("")
        st.write("")
        st.button("🎲 I'm Feeling Lucky", on_click=set_random_name, help="Randomly selects an interesting artist!")

    if name_input:
        person_noms = session.query(func.count(OscarNomination.id)).filter(OscarNomination.name == name_input).scalar()

        if person_noms == 0:
            st.warning(f"No Oscar data found for '{name_input}'")
        else:
            person_wins = session.query(func.count(OscarNomination.id)).filter(OscarNomination.name == name_input, OscarNomination.winner == True).scalar()
            
            # Percentile logic
            all_nom_counts = session.query(func.count(OscarNomination.id)).group_by(OscarNomination.name).all()
            all_counts = sorted([x[0] for x in all_nom_counts])
            percentile = sum(1 for x in all_counts if x <= person_noms) / len(all_counts) * 100

            categories = session.query(distinct(OscarNomination.canon_category)).filter(OscarNomination.name == name_input).all()
            cat_list = [c[0] for c in categories]

            first_year = session.query(func.min(OscarNomination.year_ceremony)).filter(OscarNomination.name == name_input).scalar()
            last_year = session.query(func.max(OscarNomination.year_ceremony)).filter(OscarNomination.name == name_input).scalar()
            span = last_year - first_year

            # --- DYNAMIC RANDOM FACTS BANK ---
            import random
            facts = []

            # Fact 1: Percentile & Win Rate
            p_text = f"placing them in the top {percentile:.0f}% of all Oscar-nominated individuals in history" if percentile > 50 else "making them a celebrated member of the Academy's elite"
            w_text = f"They have successfully converted those into {person_wins} win(s)!" if person_wins > 0 else "However, they have yet to secure a win."
            facts.append(f"**{name_input}** has {person_noms} total nominations, {p_text}. {w_text}")

            # Fact 2: Category Spread
            if len(cat_list) > 1:
                facts.append(f"Extremely versatile, **{name_input}** has been nominated across **{len(cat_list)} distinct Oscar categories** throughout their career! These include: {', '.join(cat_list)}.")
            else:
                facts.append(f"A master of their specific craft, **{name_input}** has built an incredible and focused legacy strictly in the **{cat_list[0]}** category across all {person_noms} of their nominations.")

            # Fact 3: Career Longevity
            if span > 10:
                facts.append(f"**{name_input}** has had incredible career longevity! Their Oscar journey spans over **{span} years**, from their very first recognition in {first_year} all the way to {last_year}.")
            elif span == 0 and person_noms > 1:
                facts.append(f"**{name_input}** accomplished the extremely rare feat of receiving {person_noms} simultaneous nominations in a single year ({first_year})!")
                
            # Fact 4: Winning efficiency
            if person_wins > 0 and person_wins == person_noms:
                facts.append(f"**{name_input}** has a flawless 100% win rate at the Oscars! Every single time they were nominated ({person_noms} times), they walked away with the prestigious trophy.")

            # Pick a random fact to display
            selected_fact = random.choice(facts)
            st.success(f"🌟 **Did You Know?**\n\n{selected_fact}")

    session.close()
