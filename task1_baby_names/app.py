"""
Task 1: Baby Names Explorer
Interactive Streamlit app using SQLite for US Baby Names data.
"""
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "baby_names.db")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "NationalNames.csv")


def init_db():
    """Load CSV into SQLite and create indexes."""
    if os.path.exists(DB_PATH):
        return
    st.info("Loading data into SQLite (first run only)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table with schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS baby_names (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            year INTEGER NOT NULL,
            gender TEXT NOT NULL CHECK(gender IN ('M', 'F')),
            count INTEGER NOT NULL
        )
    """)

    # Load data in chunks for efficiency
    chunk_size = 50000
    for chunk in pd.read_csv(DATA_PATH, chunksize=chunk_size):
        chunk.columns = ['id', 'name', 'year', 'gender', 'count']
        chunk.to_sql('baby_names', conn, if_exists='append', index=False)

    # Create indexes
    # Index 1: On (name, year) - speeds up name popularity lookups over time
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_name_year ON baby_names(name, year)")
    # Index 2: On (year, gender) - speeds up year-based aggregation queries and gender filtering
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_year_gender ON baby_names(year, gender)")

    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect(DB_PATH)


def run_query(query, params=None):
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()


# ============================================================
# Streamlit App
# ============================================================
st.set_page_config(page_title="Baby Names Explorer", page_icon="👶", layout="wide")

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #888;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">👶 Baby Names Explorer</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Explore US Baby Name Trends from 1880 to 2014</p>', unsafe_allow_html=True)

# Initialize database
init_db()

# Sidebar navigation
tab = st.sidebar.radio("Navigate", [
    "📈 Name Popularity Over Time",
    "🔍 Custom SQL Query Panel",
    "📊 Name Diversity Over Time",
    "🔬 Pattern Discovery"
])

# ============================================================
# A: Name Popularity Over Time
# ============================================================
if tab == "📈 Name Popularity Over Time":
    st.header("📈 Name Popularity Over Time")

    col1, col2 = st.columns([2, 1])
    with col1:
        name_input = st.text_input("Enter a baby name:", value="Mary")
    with col2:
        mode = st.radio("Display mode:", ["Raw Count", "Percentage"], horizontal=True)

    if name_input:
        names_list = [n.strip() for n in name_input.split(',')]
        placeholders = ', '.join(['?'] * len(names_list))

        if mode == "Raw Count":
            query = f"""
                SELECT name, year, gender, SUM(count) as total
                FROM baby_names
                WHERE name COLLATE NOCASE IN ({placeholders})
                GROUP BY name, year, gender
                ORDER BY year
            """
            df = run_query(query, names_list)
            if df.empty:
                st.warning(f"No data found for name(s) '{name_input}'")
            else:
                df['name_gender'] = df['name'] + ' (' + df['gender'] + ')'
                fig = px.line(df, x='year', y='total', color='name_gender',
                              title=f"Popularity of '{name_input}' Over Time (Raw Count)",
                              labels={'year': 'Year', 'total': 'Number of Babies', 'name_gender': 'Name (Gender)'})
                fig.update_layout(template="plotly_dark", hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)

                # Show summary stats
                col1, col2, col3 = st.columns(3)
                total_count = df['total'].sum()
                peak_row = df.loc[df['total'].idxmax()]
                col1.metric("Total Babies Named", f"{total_count:,}")
                col2.metric("Peak Year", int(peak_row['year']))
                col3.metric("Peak Count", f"{int(peak_row['total']):,} ({peak_row['name_gender']})")

        else:  # Percentage mode
            query = f"""
                SELECT bn.name, bn.year, bn.gender, 
                       SUM(bn.count) as name_count,
                       yearly.yearly_total,
                       ROUND(CAST(SUM(bn.count) AS REAL) / yearly.yearly_total * 100, 4) as percentage
                FROM baby_names bn
                JOIN (
                    SELECT year, gender, SUM(count) as yearly_total
                    FROM baby_names
                    GROUP BY year, gender
                ) yearly ON bn.year = yearly.year AND bn.gender = yearly.gender
                WHERE bn.name COLLATE NOCASE IN ({placeholders})
                GROUP BY bn.name, bn.year, bn.gender
                ORDER BY bn.year
            """
            df = run_query(query, names_list)
            if df.empty:
                st.warning(f"No data found for name(s) '{name_input}'")
            else:
                df['name_gender'] = df['name'] + ' (' + df['gender'] + ')'
                fig = px.line(df, x='year', y='percentage', color='name_gender',
                              title=f"Popularity of '{name_input}' Over Time (% of All Babies)",
                              labels={'year': 'Year', 'percentage': 'Percentage (%)', 'name_gender': 'Name (Gender)'})
                fig.update_layout(template="plotly_dark", hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)

# ============================================================
# B: Custom SQL Query Panel
# ============================================================
elif tab == "🔍 Custom SQL Query Panel":
    st.header("🔍 Custom SQL Query Panel")
    st.markdown("Write your own **SELECT** queries against the `baby_names` table.")
    st.markdown("**Schema:** `baby_names(id, name, year, gender, count)`")

    # Pre-built example buttons
    st.subheader("Quick Examples")
    col1, col2, col3 = st.columns(3)

    if "sql_query" not in st.session_state:
        st.session_state.sql_query = "SELECT name, SUM(count) as total_births FROM baby_names WHERE year = 2000 GROUP BY name ORDER BY total_births DESC LIMIT 10"
    if "last_run_query" not in st.session_state:
        st.session_state.last_run_query = None

    # Pre-built example buttons
    st.subheader("Quick Examples")
    col1, col2, col3 = st.columns(3)

    example_queries = {
        "80s Top Boy Names": "SELECT name, SUM(count) as total FROM baby_names WHERE gender = 'M' AND year BETWEEN 1980 AND 1989 GROUP BY name ORDER BY total DESC LIMIT 5",
        "Total Births by Year": "SELECT year, SUM(count) as total_births FROM baby_names GROUP BY year ORDER BY year",
        "All-Time Gender Split": "SELECT gender, SUM(count) as total FROM baby_names GROUP BY gender"
    }

    with col1:
        if st.button("👦 80s Top Boy Names"):
            st.session_state.sql_query = example_queries["80s Top Boy Names"]
    with col2:
        if st.button("📈 Total Births by Year"):
            st.session_state.sql_query = example_queries["Total Births by Year"]
    with col3:
        if st.button("⚖️ All-Time Gender Split"):
            st.session_state.sql_query = example_queries["All-Time Gender Split"]

    query_input = st.text_area("Enter your SQL query:", key="sql_query", height=120)

    if st.button("▶ Run Query", type="primary"):
        # Safety check: only SELECT
        stripped = query_input.strip().upper()
        if not stripped.startswith("SELECT"):
            st.error("⚠️ Only SELECT queries are allowed! For safety, we don't permit INSERT, UPDATE, DELETE, DROP, or any other modification queries. Please write a SELECT query to explore the data.")
            st.session_state.last_run_query = None
        else:
            st.session_state.last_run_query = query_input

    if st.session_state.last_run_query:
        try:
            result = run_query(st.session_state.last_run_query)
            st.success(f"Query returned {len(result)} rows")
            st.dataframe(result, use_container_width=True)

            # Offer chart visualization
            numeric_cols = result.select_dtypes(include='number').columns.tolist()
            all_cols = result.columns.tolist()
            
            # Require at least one numeric column, and at least 2 columns total
            if len(numeric_cols) >= 1 and len(all_cols) >= 2:
                st.subheader("📊 Visualize Results")
                
                chart_col1, chart_col2, chart_col3 = st.columns(3)
                with chart_col1:
                    chart_type = st.selectbox("Chart type:", ["Bar", "Line", "Pie"])
                with chart_col2:
                    y_col = st.selectbox("Y-axis (Numeric):", numeric_cols)
                with chart_col3:
                    x_cols_available = [c for c in all_cols if c != y_col]
                    x_col = st.selectbox("X-axis/Labels:", x_cols_available)

                if chart_type == "Bar":
                    fig = px.bar(result, x=x_col, y=y_col, title="Query Results")
                elif chart_type == "Line":
                    fig = px.line(result, x=x_col, y=y_col, title="Query Results", markers=True)
                else: # Pie
                    fig = px.pie(result, names=x_col, values=y_col, title="Query Results")
                
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Query Error: {e}")

# ============================================================
# C: Name Diversity Over Time
# ============================================================
elif tab == "📊 Name Diversity Over Time":
    st.header("📊 Name Diversity Over Time")
    st.markdown("How many unique names are used each year? Is naming becoming more diverse?")

    query = """
        SELECT year, COUNT(DISTINCT name) as unique_names, SUM(count) as total_babies
        FROM baby_names
        GROUP BY year
        ORDER BY year
    """
    df = run_query(query)

    fig = px.area(df, x='year', y='unique_names',
                  title="Number of Unique Baby Names Per Year",
                  labels={'year': 'Year', 'unique_names': 'Unique Names'},
                  color_discrete_sequence=['#4ECDC4'])
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # Also show by gender
    query_gender = """
        SELECT year, gender, COUNT(DISTINCT name) as unique_names
        FROM baby_names
        GROUP BY year, gender
        ORDER BY year
    """
    df_gender = run_query(query_gender)
    fig2 = px.line(df_gender, x='year', y='unique_names', color='gender',
                   title="Unique Names by Gender Over Time",
                   labels={'year': 'Year', 'unique_names': 'Unique Names', 'gender': 'Gender'},
                   color_discrete_map={'F': '#FF6B6B', 'M': '#4ECDC4'})
    fig2.update_layout(template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)

    # Gender-neutral name finder
    st.subheader("⚖️ Gender-Neutral Name Finder")
    st.markdown("Names that are commonly used for both boys and girls:")

    query_neutral = """
        SELECT name,
               SUM(CASE WHEN gender='F' THEN count ELSE 0 END) as female_count,
               SUM(CASE WHEN gender='M' THEN count ELSE 0 END) as male_count,
               SUM(count) as total,
               ROUND(
                   MIN(SUM(CASE WHEN gender='F' THEN count ELSE 0 END), SUM(CASE WHEN gender='M' THEN count ELSE 0 END)) * 100.0 /
                   MAX(SUM(CASE WHEN gender='F' THEN count ELSE 0 END), SUM(CASE WHEN gender='M' THEN count ELSE 0 END)),
               1) as balance_ratio
        FROM baby_names
        GROUP BY name
        HAVING female_count > 1000 AND male_count > 1000
        ORDER BY balance_ratio DESC
        LIMIT 20
    """
    df_neutral = run_query(query_neutral)
    if not df_neutral.empty:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name='Female', x=df_neutral['name'], y=df_neutral['female_count'],
                              marker_color='#FF6B6B'))
        fig3.add_trace(go.Bar(name='Male', x=df_neutral['name'], y=df_neutral['male_count'],
                              marker_color='#4ECDC4'))
        fig3.update_layout(barmode='group', title="Most Gender-Neutral Names",
                           template="plotly_dark",
                           xaxis_title="Name", yaxis_title="Total Count")
        st.plotly_chart(fig3, use_container_width=True)

# ============================================================
# Pattern Discovery
# ============================================================
elif tab == "🔬 Pattern Discovery":
    st.header("🔬 Pattern Discovery")
    st.markdown("Three interesting patterns found in the US Baby Names data:")

    # Pattern 1: Declining dominance of top names
    st.subheader("Pattern 1: The Decline of Dominant Names")
    query1 = """
        SELECT year,
               MAX(count) as top_name_count,
               SUM(count) as total_babies,
               ROUND(MAX(count) * 100.0 / SUM(count), 2) as top_pct
        FROM baby_names
        WHERE gender = 'F'
        GROUP BY year
        ORDER BY year
    """
    df1 = run_query(query1)
    fig1 = px.line(df1, x='year', y='top_pct',
                   title="Percentage of Babies with the #1 Most Popular Female Name",
                   labels={'year': 'Year', 'top_pct': '% of All Female Babies'},
                   color_discrete_sequence=['#FF6B6B'])
    fig1.update_layout(template="plotly_dark")
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown("""
    **Finding:** The most popular female name in any given year used to account for almost 6% of all girls born (e.g., Mary in the early 1900s), 
    but by 2014 the top name captures less than 1% of babies. This shows a massive cultural shift toward 
    individuality in naming. Parents today are much less likely to follow a single dominant trend and instead 
    pick from a hugely expanded pool of names. This likely reflects broader social changes where uniqueness 
    and personal identity became more valued over conformity.
    """)

    # Pattern 2: Name popularity spikes (celebrity effect)
    st.subheader("Pattern 2: Celebrity-Driven Name Spikes")
    celeb_names = {
        'Arya': 'Game of Thrones (2011)',
        'Khaleesi': 'Game of Thrones (2011)',
        'Elsa': 'Frozen (2013)'
    }
    query2 = """
        SELECT name, year, SUM(count) as total
        FROM baby_names
        WHERE name IN ('Arya', 'Khaleesi', 'Elsa') AND year >= 1990
        GROUP BY name, year
        ORDER BY year
    """
    df2 = run_query(query2)
    fig2 = px.line(df2, x='year', y='total', color='name',
                   title="Celebrity/Media-Driven Name Popularity Spikes",
                   labels={'year': 'Year', 'total': 'Babies Named', 'name': 'Name'})
    fig2.update_layout(template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("""
    **Finding:** Some names experience dramatic spikes tied to pop culture events. "Arya" and "Khaleesi" both shot up 
    after Game of Thrones premiered in 2011 — Khaleesi literally went from zero to hundreds of babies per year, 
    which is remarkable since it is not even a real name but a fictional title. "Elsa" saw a noticeable bump around 
    2013-2014 when the movie Frozen came out. This pattern shows how strongly media and celebrity culture 
    influence naming decisions, and these spikes tend to fade as the cultural moment passes.
    """)

    # Pattern 3: The rise of unique names
    st.subheader("Pattern 3: Explosion of Name Diversity")
    query3 = """
        SELECT year,
               COUNT(DISTINCT name) as unique_names,
               SUM(count) as total_babies,
               ROUND(COUNT(DISTINCT name) * 1.0 / (SUM(count) / 1000), 2) as names_per_1000
        FROM baby_names
        GROUP BY year
        ORDER BY year
    """
    df3 = run_query(query3)
    fig3 = px.bar(df3, x='year', y='unique_names',
                  title="Number of Unique Names Used Per Year",
                  labels={'year': 'Year', 'unique_names': 'Unique Names'},
                  color='unique_names', color_continuous_scale='viridis')
    fig3.update_layout(template="plotly_dark")
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown("""
    **Finding:** The number of unique baby names per year has grown dramatically — from about 1,000 in 1880 
    to over 30,000 by 2014. This is not just because more babies are born; the ratio of unique names to total 
    babies has increased significantly. This explosion in diversity reflects immigration bringing names from 
    many cultures, parents inventing new names or creative spellings, and a cultural move away from traditional 
    naming conventions. It suggests that American society has become much more open to diversity and 
    individual expression in something as fundamental as what we call our children.
    """)
