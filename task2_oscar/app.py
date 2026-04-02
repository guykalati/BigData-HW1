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

    # ---- CATEGORY WHITELIST APPROACH ----
    # Instead of trying to blacklist bad names (which always misses edge cases),
    # we whitelist the categories that are guaranteed to contain individual people.
    PERSON_CATEGORIES = [
        'ACTOR', 'ACTOR IN A LEADING ROLE', 'ACTOR IN A SUPPORTING ROLE',
        'ACTRESS', 'ACTRESS IN A LEADING ROLE', 'ACTRESS IN A SUPPORTING ROLE',
        'DIRECTING', 'DIRECTING (Comedy Picture)', 'DIRECTING (Dramatic Picture)',
        'WRITING (Adapted Screenplay)', 'WRITING (Original Screenplay)',
        'WRITING (Original Story)', 'WRITING (Adaptation)', 'WRITING', 'WRITING (Screenplay)',
        'WRITING (Story and Screenplay)', 'WRITING (Motion Picture Story)',
        'WRITING (Screenplay--Adapted)', 'WRITING (Screenplay--Original)',
        'WRITING (Screenplay Based on Material from Another Medium)',
        'WRITING (Screenplay Written Directly for the Screen)',
        'WRITING (Screenplay--based on material from another medium)',
        'WRITING (Story and Screenplay--written directly for the screen)',
        'WRITING (Screenplay Based on Material Previously Produced or Published)',
        'WRITING (Screenplay Adapted from Other Material)',
        'WRITING (Story and Screenplay--based on material not previously published or produced)',
        'WRITING (Story and Screenplay--based on factual material or material not previously published or produced)',
        'WRITING (Screenplay Written Directly for the Screen--based on factual material or on story material not previously published or produced)',
        'WRITING (Original Motion Picture Story)',
        'CINEMATOGRAPHY', 'CINEMATOGRAPHY (Black-and-White)', 'CINEMATOGRAPHY (Color)',
        'FILM EDITING', 'MUSIC (Original Score)', 'MUSIC (Original Song)',
        'COSTUME DESIGN', 'COSTUME DESIGN (Black-and-White)', 'COSTUME DESIGN (Color)',
    ]

    all_noms = session.query(OscarNomination).filter(
        OscarNomination.canon_category.in_(PERSON_CATEGORIES)
    ).all()
    session.close()

    # Build per-person stats from whitelisted data only
    stats = {}
    categories_per_person = {}
    years_per_person = {}

    for n in all_noms:
        # Extra safety: skip any name containing '/' (multi-person credits)
        if '/' in n.name:
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

    # ---- Find 1: The Biggest Snubs (Most Noms Without a Win) ----
    st.subheader("1. The Biggest Snubs (Most Nominations, Zero Wins)")
    snubs = [
        {'Name': name, 'Nominations': data['noms']}
        for name, data in stats.items()
        if data['wins'] == 0 and data['noms'] >= 3
    ]
    snubs = sorted(snubs, key=lambda x: x['Nominations'], reverse=True)[:10]

    df1 = pd.DataFrame(snubs)
    fig1 = px.bar(df1, x='Name', y='Nominations',
                  title="The Biggest Oscar Snubs: Most Nominations Without a Single Win 😤",
                  color='Nominations', color_continuous_scale='Reds')
    fig1.update_layout(template="plotly_dark")
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown("""
    **Finding:** Being repeatedly nominated but never winning is one of the most heartbreaking 
    stories in Oscar history. These actors, directors, and writers have been recognized multiple times 
    as among the very best of the year—yet the final trophy has always eluded them. It highlights 
    how competitive the Academy Awards truly are.
    """)

    # ---- Find 2: Versatile Visionaries (Treemap) ----
    st.subheader("2. The Versatile Visionaries")
    versatile = [
        {'Name': name, 'Unique Categories': len(cats), 'Categories': ", ".join(sorted(cats))}
        for name, cats in categories_per_person.items()
        if len(cats) >= 2
    ]
    versatile = sorted(versatile, key=lambda x: x['Unique Categories'], reverse=True)[:10]

    # Treemap data: each person gets a box sized by their category count
    treemap_data = []
    for v in versatile:
        for cat in categories_per_person[v['Name']]:
            treemap_data.append({'Artist': v['Name'], 'Category': cat, 'Value': 1})
    df2 = pd.DataFrame(treemap_data)
    fig2 = px.treemap(df2, path=['Artist', 'Category'], values='Value',
                      title="Versatile Artists and Their Oscar Categories 🎭",
                      color_discrete_sequence=px.colors.qualitative.Set3)
    fig2.update_layout(template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("""
    **Finding:** Most artists specialize in one craft, but a select few are true Renaissance people. 
    This treemap shows the top 10 most versatile Oscar nominees. Each colored block represents a 
    distinct category they were nominated in—the more blocks, the more diverse their talent. Click 
    on any artist to zoom in and see their full category breakdown.
    """)

    # ---- Find 3: Decade Dominators ----
    st.subheader("3. The 'Decade Dominators'")
    decade_stats = {}
    for name, yrs in years_per_person.items():
        decades = set((y // 10) * 10 for y in yrs)
        if len(decades) >= 2:
            decade_stats[name] = {'Decades Active': len(decades), 'Total Noms': len(yrs),
                                  'Decade List': ", ".join(f"{d}s" for d in sorted(decades))}

    dominators = sorted(decade_stats.items(), key=lambda x: (x[1]['Decades Active'], x[1]['Total Noms']), reverse=True)[:10]
    df3 = pd.DataFrame([{'Name': n, **d} for n, d in dominators])

    fig3 = px.bar(df3, x='Decades Active', y='Name', orientation='h',
                  text='Decades Active', hover_data=['Decade List', 'Total Noms'],
                  title="Artists Nominated Across the Most Distinct Decades 📆",
                  color='Total Noms', color_continuous_scale='Purples')
    fig3.update_traces(textposition='inside')
    fig3.update_layout(yaxis={'categoryorder': 'total ascending'}, template="plotly_dark")
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown("""
    **Finding:** Staying relevant in Hollywood for one decade is hard. Staying relevant across 
    multiple decades is legendary. These artists didn't just have one era of greatness—they earned 
    Oscar nominations across completely different decades, proving their talent transcends generational 
    trends and shifting industry tastes.
    """)


# ============================================================
# Bonus: Did You Know?
# ============================================================
elif tab == "🎲 Did You Know?":
    st.header("🎲 Did You Know?")

    session = Session()

    # Use the same whitelist approach for the dropdown
    PERSON_CATEGORIES = [
        'ACTOR', 'ACTOR IN A LEADING ROLE', 'ACTOR IN A SUPPORTING ROLE',
        'ACTRESS', 'ACTRESS IN A LEADING ROLE', 'ACTRESS IN A SUPPORTING ROLE',
        'DIRECTING', 'DIRECTING (Comedy Picture)', 'DIRECTING (Dramatic Picture)',
        'WRITING (Adapted Screenplay)', 'WRITING (Original Screenplay)',
        'WRITING (Original Story)', 'WRITING (Adaptation)', 'WRITING', 'WRITING (Screenplay)',
        'CINEMATOGRAPHY', 'CINEMATOGRAPHY (Black-and-White)', 'CINEMATOGRAPHY (Color)',
        'FILM EDITING', 'MUSIC (Original Score)', 'MUSIC (Original Song)',
        'COSTUME DESIGN', 'COSTUME DESIGN (Black-and-White)', 'COSTUME DESIGN (Color)',
    ]

    raw_names = [r[0] for r in session.query(distinct(OscarNomination.name)).filter(
        OscarNomination.canon_category.in_(PERSON_CATEGORIES)
    ).all()]
    all_names = sorted([n for n in raw_names if '/' not in n])

    if "dyk_name" not in st.session_state:
        st.session_state.dyk_name = "Meryl Streep" if "Meryl Streep" in all_names else all_names[0]

    def set_random_name():
        import random
        multi_noms = session.query(OscarNomination.name).filter(
            OscarNomination.canon_category.in_(PERSON_CATEGORIES)
        ).group_by(OscarNomination.name).having(func.count(OscarNomination.id) > 1).all()
        multi_list = sorted([r[0] for r in multi_noms if '/' not in r[0]])
        st.session_state.dyk_name = random.choice(multi_list) if multi_list else random.choice(all_names)

    col1, col2 = st.columns([3, 1])
    with col1:
        name_input = st.selectbox("Select an actor/director for a fun fact:", options=all_names, key="dyk_name")
    with col2:
        st.write("")
        st.write("")
        st.button("🎲 I'm Feeling Lucky", on_click=set_random_name, help="Randomly selects an interesting artist!")

    if name_input:
        # Query only whitelisted categories for this person
        person_noms_q = session.query(OscarNomination).filter(
            OscarNomination.name == name_input,
            OscarNomination.canon_category.in_(PERSON_CATEGORIES)
        ).all()
        person_noms = len(person_noms_q)

        if person_noms == 0:
            st.warning(f"No Oscar data found for '{name_input}'")
        else:
            person_wins = sum(1 for n in person_noms_q if n.winner)

            # Percentile logic
            all_nom_counts = session.query(func.count(OscarNomination.id)).filter(
                OscarNomination.canon_category.in_(PERSON_CATEGORIES)
            ).group_by(OscarNomination.name).all()
            all_counts = sorted([x[0] for x in all_nom_counts])
            percentile = sum(1 for x in all_counts if x <= person_noms) / len(all_counts) * 100

            cat_list = list(set(n.canon_category for n in person_noms_q))
            years = [n.year_ceremony for n in person_noms_q]
            first_year = min(years)
            last_year = max(years)
            span = last_year - first_year
            films = list(set(n.film for n in person_noms_q if n.film))

            # --- DYNAMIC RANDOM FACTS BANK ---
            import random
            facts = []

            # Fact 1: Percentile & Win Rate
            p_text = f"placing them in the top **{percentile:.0f}%** of all Oscar-nominated individuals in history" if percentile > 50 else "making them a celebrated member of the Academy's elite"
            w_text = f"They have successfully converted those into **{person_wins} win(s)**!" if person_wins > 0 else "However, they have yet to secure a win."
            facts.append(f"**{name_input}** has **{person_noms}** competitive nominations, {p_text}. {w_text}")

            # Fact 2: Category Spread
            if len(cat_list) > 1:
                facts.append(f"Extremely versatile, **{name_input}** has been nominated across **{len(cat_list)} distinct Oscar categories**: {', '.join(cat_list)}. That's rare—most people spend their entire career in just one!")
            else:
                facts.append(f"A master of their craft, **{name_input}** has built their entire Oscar legacy in the **{cat_list[0]}** category, earning all {person_noms} of their nominations there.")

            # Fact 3: Career Longevity
            if span > 10:
                facts.append(f"Talk about staying power! **{name_input}**'s Oscar journey spans an incredible **{span} years**, from {first_year} all the way to {last_year}.")
            elif span == 0 and person_noms > 1:
                facts.append(f"**{name_input}** pulled off the rare feat of receiving **{person_noms} nominations in the very same year** ({first_year})!")

            # Fact 4: Winning efficiency
            if person_wins > 0 and person_wins == person_noms:
                facts.append(f"Incredible: **{name_input}** has a flawless **100% win rate** at the Oscars! They were nominated {person_noms} time(s) and won every single time.")
            elif person_wins > 0:
                win_rate = person_wins / person_noms * 100
                facts.append(f"**{name_input}** has a **{win_rate:.0f}% win rate** ({person_wins} wins from {person_noms} nominations). For comparison, the average Oscar nominee wins about 20% of the time.")

            # Fact 5: Film count
            if len(films) > 3:
                facts.append(f"Over their career, **{name_input}** has been recognized for their work in **{len(films)} different films** at the Oscars, including titles like *{films[0]}* and *{films[1]}*.")

            # Fact 6: Decade spread
            decades = set((y // 10) * 10 for y in years)
            if len(decades) >= 3:
                decade_str = ", ".join(f"{d}s" for d in sorted(decades))
                facts.append(f"**{name_input}** has been nominated across **{len(decades)} different decades** ({decade_str}), proving their talent truly transcends generational trends.")

            # Pick a random fact to display
            selected_fact = random.choice(facts)
            st.success(f"🌟 **Did You Know?**\n\n{selected_fact}")

    session.close()
