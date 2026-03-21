"""
Task 4: SQL Learning Game - "Detective SQL: Case Files"
An interactive, story-driven SQL learning platform where you're a detective
solving mysteries by querying an evidence database.
"""
import streamlit as st
import sqlite3
import pandas as pd
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "detective.db")


def init_db():
    """Create the detective game database with crime-themed tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Suspects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suspects (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            occupation TEXT,
            city TEXT,
            has_alibi BOOLEAN,
            criminal_record BOOLEAN
        )
    """)

    # Crime scenes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crime_scenes (
            id INTEGER PRIMARY KEY,
            location TEXT NOT NULL,
            crime_type TEXT,
            date TEXT,
            city TEXT,
            evidence_found TEXT
        )
    """)

    # Evidence table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY,
            crime_scene_id INTEGER,
            type TEXT,
            description TEXT,
            suspect_id INTEGER,
            FOREIGN KEY (crime_scene_id) REFERENCES crime_scenes(id),
            FOREIGN KEY (suspect_id) REFERENCES suspects(id)
        )
    """)

    # Witness statements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS witnesses (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            crime_scene_id INTEGER,
            statement TEXT,
            reliability TEXT,
            FOREIGN KEY (crime_scene_id) REFERENCES crime_scenes(id)
        )
    """)

    # Insert sample data - suspects
    suspects_data = [
        (1, 'Marcus Black', 35, 'Banker', 'New York', 0, 1),
        (2, 'Elena Rossi', 28, 'Artist', 'New York', 1, 0),
        (3, 'James Carter', 42, 'Lawyer', 'Chicago', 0, 0),
        (4, 'Sophia Chen', 31, 'Doctor', 'New York', 1, 0),
        (5, 'Victor Crane', 55, 'CEO', 'Los Angeles', 0, 1),
        (6, 'Luna Martinez', 24, 'Student', 'Chicago', 1, 0),
        (7, 'Robert Wolf', 48, 'Detective', 'New York', 0, 0),
        (8, 'Aria Frost', 33, 'Journalist', 'Los Angeles', 0, 1),
        (9, 'David Kim', 39, 'Chef', 'Chicago', 1, 0),
        (10, 'Grace Turner', 29, 'Nurse', 'New York', 0, 0),
        (11, 'Leo Moretti', 45, 'Politician', 'Los Angeles', 0, 1),
        (12, 'Nina Volkov', 37, 'Scientist', 'Chicago', 1, 0),
    ]

    # Crime scenes
    scenes_data = [
        (1, 'Central Park', 'Theft', '2024-01-15', 'New York', 'Fingerprints on safe'),
        (2, 'Grand Hotel', 'Fraud', '2024-02-20', 'New York', 'Forged documents'),
        (3, 'City Museum', 'Theft', '2024-03-10', 'Chicago', 'Security footage'),
        (4, 'Harbor Warehouse', 'Smuggling', '2024-01-30', 'Los Angeles', 'Hidden compartments'),
        (5, 'Downtown Office', 'Embezzlement', '2024-04-05', 'New York', 'Altered records'),
        (6, 'Lake Shore', 'Theft', '2024-03-22', 'Chicago', 'Footprints'),
    ]

    # Evidence
    evidence_data = [
        (1, 1, 'Fingerprint', 'Partial fingerprint on the safe lock', 1),
        (2, 1, 'Fiber', 'Black wool fiber from expensive coat', 5),
        (3, 2, 'Document', 'Forged bank transfer documents', 3),
        (4, 2, 'Digital', 'Login records from hotel business center', 1),
        (5, 3, 'Video', 'Blurry figure on security camera', 8),
        (6, 3, 'Fingerprint', 'Fingerprint on display case', 6),
        (7, 4, 'Physical', 'Hidden compartment with contraband', 5),
        (8, 4, 'Document', 'Shipping manifest with false entries', 11),
        (9, 5, 'Digital', 'Modified financial records', 3),
        (10, 5, 'Document', 'Falsified expense reports', 11),
        (11, 6, 'Footprint', 'Size 11 boot prints near the scene', 7),
        (12, 6, 'Fiber', 'Blue denim fibers caught on fence', None),
    ]

    # Witnesses
    witnesses_data = [
        (1, 'John Park', 1, 'I saw a tall man in a dark coat running from the park around 11 PM', 'High'),
        (2, 'Mary Lane', 1, 'I heard glass breaking but did not see anyone', 'Medium'),
        (3, 'Tom Bell', 2, 'A man in a suit was using the business center late at night', 'High'),
        (4, 'Sarah Lee', 3, 'I saw someone carrying a large bag out the back door', 'Medium'),
        (5, 'Mike Ross', 4, 'Trucks were coming and going at unusual hours', 'High'),
        (6, 'Anna Kim', 5, 'I noticed the accounting files were moved', 'Low'),
        (7, 'Chris Day', 6, 'Two people were arguing near the lake at midnight', 'Medium'),
        (8, 'Pat Quinn', 2, 'The hotel safe was open when I came in for my shift', 'High'),
    ]

    cursor.execute("DELETE FROM suspects")
    cursor.execute("DELETE FROM crime_scenes")
    cursor.execute("DELETE FROM evidence")
    cursor.execute("DELETE FROM witnesses")

    cursor.executemany("INSERT INTO suspects VALUES (?,?,?,?,?,?,?)", suspects_data)
    cursor.executemany("INSERT INTO crime_scenes VALUES (?,?,?,?,?,?)", scenes_data)
    cursor.executemany("INSERT INTO evidence VALUES (?,?,?,?,?)", evidence_data)
    cursor.executemany("INSERT INTO witnesses VALUES (?,?,?,?,?)", witnesses_data)

    conn.commit()
    conn.close()


# ============================================================
# Level Definitions
# ============================================================
LEVELS = [
    {
        "level": 1,
        "title": "🔍 Level 1: First Day on the Job — SELECT *",
        "concept": "SELECT basics",
        "story": """Welcome, Detective! You have just been assigned to the Cold Cases unit. 
Your first task is simple — get familiar with the suspects in our database. 
Every investigation starts with knowing who you are dealing with.""",
        "challenge": "Retrieve ALL columns for ALL suspects from the `suspects` table.",
        "hint": "Use `SELECT * FROM table_name` to see everything in a table. The table you need is called 'suspects'.",
        "check_query": "SELECT * FROM suspects",
        "validate": lambda result, expected: len(result) == len(expected) and set(result.columns) == set(expected.columns),
        "expected_rows": 12,
    },
    {
        "level": 2,
        "title": "🕵️ Level 2: Narrowing the Search — WHERE",
        "concept": "WHERE clause filtering",
        "story": """Good work getting the full list! But a real detective doesn't look at everyone — 
you focus on those who raise red flags. Your captain wants a list of suspects 
who DO NOT have an alibi. Those are the ones we need to watch closely.""",
        "challenge": "Find all suspects who do NOT have an alibi (`has_alibi = 0`). Show their name, occupation, and city.",
        "hint": "Use `SELECT column1, column2 FROM table WHERE condition`. The column for alibi is 'has_alibi' and you want rows where it equals 0.",
        "check_query": "SELECT name, occupation, city FROM suspects WHERE has_alibi = 0",
        "validate": lambda result, expected: len(result) == len(expected),
        "expected_rows": 7,
    },
    {
        "level": 3,
        "title": "📋 Level 3: Organizing the Evidence — ORDER BY & LIMIT",
        "concept": "ORDER BY and LIMIT",
        "story": """A new lead has come in! We need to focus on the most recent crimes first. 
Your job is to check the crime scenes, starting from the most recent one, 
but the captain only wants to see the 3 most recent cases to start with.""",
        "challenge": "Get all columns from `crime_scenes`, ordered by date from newest to oldest, and show only the top 3.",
        "hint": "Use `ORDER BY column DESC` to sort from newest to oldest, and `LIMIT N` to restrict the number of rows.",
        "check_query": "SELECT * FROM crime_scenes ORDER BY date DESC LIMIT 3",
        "validate": lambda result, expected: len(result) == 3,
        "expected_rows": 3,
    },
    {
        "level": 4,
        "title": "📊 Level 4: Patterns in Crime — GROUP BY & COUNT",
        "concept": "GROUP BY with aggregations",
        "story": """The police chief has noticed that some cities seem to have more crime than others. 
She wants you to analyze the data and figure out how many crimes happened in each city. 
This kind of pattern recognition is what separates good detectives from great ones.""",
        "challenge": "Count the number of crime scenes in each city. Show the city name and the count, and name the count column `crime_count`.",
        "hint": "Use `SELECT column, COUNT(*) as alias FROM table GROUP BY column` to count rows per group.",
        "check_query": "SELECT city, COUNT(*) as crime_count FROM crime_scenes GROUP BY city",
        "validate": lambda result, expected: len(result) == len(expected) and 'crime_count' in [c.lower() for c in result.columns],
        "expected_rows": 3,
    },
    {
        "level": 5,
        "title": "🔗 Level 5: Connecting the Dots — JOIN",
        "concept": "JOIN operations",
        "story": """This is the big one, Detective. We have evidence linked to crime scenes, but we need 
to see the full picture. The forensics team needs a report that shows each piece of evidence 
alongside the crime scene location where it was found. Time to connect the tables!""",
        "challenge": "Join the `evidence` table with `crime_scenes` table to show each evidence's `type`, `description`, and the `location` of the crime scene where it was found. Use `crime_scene_id` to connect them.",
        "hint": "Use `SELECT columns FROM table1 JOIN table2 ON table1.foreign_key = table2.primary_key`. Connect evidence.crime_scene_id to crime_scenes.id.",
        "check_query": "SELECT e.type, e.description, cs.location FROM evidence e JOIN crime_scenes cs ON e.crime_scene_id = cs.id",
        "validate": lambda result, expected: len(result) == len(expected),
        "expected_rows": 12,
    },
    {
        "level": 6,
        "title": "🎯 Level 6: The Final Deduction — Complex Query",
        "concept": "Combining WHERE, JOIN, and aggregation",
        "story": """It all comes down to this, Detective. We need to find which suspects are connected 
to the most pieces of evidence. The suspect with the most evidence against them is our 
prime target. Write one query to crack the case!""",
        "challenge": "Find suspects linked to evidence: join `evidence` with `suspects` (on evidence.suspect_id = suspects.id), group by suspect name, count the evidence pieces as `evidence_count`, and order by count descending.",
        "hint": "Combine JOIN, GROUP BY, COUNT, and ORDER BY. Join evidence to suspects using suspect_id, group by name, count the rows, and order descending.",
        "check_query": "SELECT s.name, COUNT(*) as evidence_count FROM evidence e JOIN suspects s ON e.suspect_id = s.id GROUP BY s.name ORDER BY evidence_count DESC",
        "validate": lambda result, expected: len(result) > 0 and len(result) == len(expected),
        "expected_rows": None,  # Dynamic
    },
    {
        "level": 7,
        "title": "🏆 Level 7: Bonus — Subqueries & Advanced Analysis",
        "concept": "Subqueries and advanced SQL",
        "story": """Congratulations, Detective — you have proven yourself! For your final challenge, 
we need you to find suspects who have NO alibi AND are linked to evidence at crime scenes 
in New York. This requires combining everything you have learned.""",
        "challenge": "Find the names of suspects who have `has_alibi = 0` AND appear in the evidence table linked to crime scenes in 'New York'. Show suspect name and crime scene location.",
        "hint": "You need a multi-table JOIN: suspects → evidence → crime_scenes. Then filter with WHERE for has_alibi = 0 AND city = 'New York'.",
        "check_query": "SELECT DISTINCT s.name, cs.location FROM suspects s JOIN evidence e ON s.id = e.suspect_id JOIN crime_scenes cs ON e.crime_scene_id = cs.id WHERE s.has_alibi = 0 AND cs.city = 'New York'",
        "validate": lambda result, expected: len(result) == len(expected),
        "expected_rows": None,
    }
]


# ============================================================
# Streamlit App
# ============================================================
st.set_page_config(page_title="Detective SQL", page_icon="🕵️", layout="wide")

st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00b4d8, #0077b6, #023e8a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    .story-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-left: 4px solid #00b4d8;
        padding: 1.5rem;
        border-radius: 0 10px 10px 0;
        margin: 1rem 0;
        font-style: italic;
    }
    .challenge-box {
        background: linear-gradient(135deg, #2d2d2d 0%, #0d1117 100%);
        border: 2px solid #ffd700;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .hint-box {
        background: #1a3a2a;
        border-left: 4px solid #4ECDC4;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
        margin: 0.5rem 0;
    }
    .success-animation {
        font-size: 3rem;
        text-align: center;
        animation: pulse 1s ease-in-out;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.2); }
        100% { transform: scale(1); }
    }
    .progress-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: bold;
        margin: 0.2rem;
    }
    .completed {
        background: #1a5e2a;
        color: #4ECDC4;
    }
    .current {
        background: #5e4a1a;
        color: #FFD700;
    }
    .locked {
        background: #333;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🕵️ Detective SQL: Case Files</p>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#888; font-size:1.2rem'>Solve crimes by mastering SQL queries</p>", unsafe_allow_html=True)

# Initialize database and session state
init_db()

if 'completed_levels' not in st.session_state:
    st.session_state['completed_levels'] = set()
if 'current_level' not in st.session_state:
    st.session_state['current_level'] = 1
if 'attempts' not in st.session_state:
    st.session_state['attempts'] = {}
if 'points' not in st.session_state:
    st.session_state['points'] = 0
if 'streak' not in st.session_state:
    st.session_state['streak'] = 0

# Sidebar - Progress Tracking
st.sidebar.header("📊 Detective Progress")
st.sidebar.metric("🏅 Points", st.session_state['points'])
st.sidebar.metric("🔥 Streak", st.session_state['streak'])
st.sidebar.divider()

# Show level progress
st.sidebar.subheader("📋 Case Files")
for level_info in LEVELS:
    lvl = level_info['level']
    if lvl in st.session_state['completed_levels']:
        st.sidebar.markdown(f"<span class='progress-badge completed'>✅ Level {lvl}</span> {level_info['concept']}", unsafe_allow_html=True)
    elif lvl == st.session_state['current_level']:
        st.sidebar.markdown(f"<span class='progress-badge current'>🔓 Level {lvl}</span> {level_info['concept']}", unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"<span class='progress-badge locked'>🔒 Level {lvl}</span> {level_info['concept']}", unsafe_allow_html=True)

# Navigation
nav = st.sidebar.radio("Mode", ["🎮 Play", "📚 Database Schema", "🏆 Achievements"], label_visibility="collapsed")

if nav == "📚 Database Schema":
    st.header("📚 Database Schema")
    st.markdown("Here are the tables you'll be querying:")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("👤 suspects")
        st.code("""
id          INTEGER PRIMARY KEY
name        TEXT
age         INTEGER
occupation  TEXT
city        TEXT
has_alibi   BOOLEAN (0 or 1)
criminal_record BOOLEAN (0 or 1)
        """)

        st.subheader("📦 evidence")
        st.code("""
id              INTEGER PRIMARY KEY
crime_scene_id  INTEGER (FK → crime_scenes.id)
type            TEXT
description     TEXT
suspect_id      INTEGER (FK → suspects.id)
        """)

    with col2:
        st.subheader("🏠 crime_scenes")
        st.code("""
id              INTEGER PRIMARY KEY
location        TEXT
crime_type      TEXT
date            TEXT
city            TEXT
evidence_found  TEXT
        """)

        st.subheader("👁️ witnesses")
        st.code("""
id              INTEGER PRIMARY KEY
name            TEXT
crime_scene_id  INTEGER (FK → crime_scenes.id)
statement       TEXT
reliability     TEXT (High/Medium/Low)
        """)

    # Show actual data preview
    st.divider()
    st.subheader("🔎 Data Preview")
    conn = sqlite3.connect(DB_PATH)
    for table_name in ['suspects', 'crime_scenes', 'evidence', 'witnesses']:
        with st.expander(f"Preview: {table_name}"):
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            st.dataframe(df, use_container_width=True)
    conn.close()

elif nav == "🏆 Achievements":
    st.header("🏆 Achievements")

    achievements = [
        ("🔰 Rookie Detective", "Complete Level 1", 1 in st.session_state['completed_levels']),
        ("🕵️ Junior Investigator", "Complete Level 3", 3 in st.session_state['completed_levels']),
        ("📊 Data Analyst", "Complete Level 4 (GROUP BY)", 4 in st.session_state['completed_levels']),
        ("🔗 Connection Master", "Complete Level 5 (JOIN)", 5 in st.session_state['completed_levels']),
        ("🎯 Senior Detective", "Complete all levels", len(st.session_state['completed_levels']) == len(LEVELS)),
        ("🔥 Hot Streak", "Get 3 correct in a row", st.session_state['streak'] >= 3),
        ("💯 Point Master", "Earn 500+ points", st.session_state['points'] >= 500),
    ]

    for name, desc, earned in achievements:
        if earned:
            st.success(f"{name} — {desc} ✅")
        else:
            st.info(f"{name} — {desc} 🔒")

else:  # Play mode
    current = st.session_state['current_level']
    level_data = None
    for l in LEVELS:
        if l['level'] == current:
            level_data = l
            break

    if level_data is None:
        st.markdown('<p class="success-animation">🎉🏆🎉</p>', unsafe_allow_html=True)
        st.success("🎉 Congratulations, Detective! You've completed ALL case files! You are now a SQL Master!")
        st.balloons()
        st.markdown(f"**Final Score:** {st.session_state['points']} points")
        st.markdown(f"**Levels Completed:** {len(st.session_state['completed_levels'])}/{len(LEVELS)}")

        # Allow replaying
        if st.button("🔄 Replay from Level 1"):
            st.session_state['current_level'] = 1
            st.session_state['completed_levels'] = set()
            st.session_state['points'] = 0
            st.session_state['streak'] = 0
            st.session_state['attempts'] = {}
            st.rerun()
    else:
        st.markdown(f"## {level_data['title']}")

        # Story
        st.markdown(f'<div class="story-box">📖 {level_data["story"]}</div>', unsafe_allow_html=True)

        # Challenge
        st.markdown(f'<div class="challenge-box">🎯 <strong>Your Mission:</strong> {level_data["challenge"]}</div>', unsafe_allow_html=True)

        # Hint toggle
        with st.expander("💡 Need a hint?"):
            st.markdown(f'<div class="hint-box">{level_data["hint"]}</div>', unsafe_allow_html=True)

        # SQL Input
        query_input = st.text_area("Write your SQL query here:", height=120,
                                    key=f"query_level_{current}",
                                    placeholder="SELECT ... FROM ...")

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            run_btn = st.button("▶ Execute Query", type="primary")
        with col2:
            skip_btn = st.button("⏭️ Skip Level")

        if skip_btn:
            st.session_state['current_level'] = current + 1
            st.session_state['streak'] = 0
            st.rerun()

        if run_btn and query_input:
            # Safety: only SELECT
            stripped = query_input.strip().upper()
            if not stripped.startswith("SELECT"):
                st.error("⚠️ Only SELECT queries are allowed in this game! Don't worry — detectives observe, they don't tamper with evidence. 😉")
            else:
                try:
                    conn = sqlite3.connect(DB_PATH)

                    # Run student's query
                    student_result = pd.read_sql_query(query_input, conn)
                    # Run expected query
                    expected_result = pd.read_sql_query(level_data['check_query'], conn)
                    conn.close()

                    st.subheader("📋 Your Query Results:")
                    st.dataframe(student_result, use_container_width=True)

                    # Validate
                    is_correct = False
                    try:
                        is_correct = level_data['validate'](student_result, expected_result)
                    except:
                        is_correct = len(student_result) == len(expected_result)

                    if is_correct:
                        st.markdown('<p class="success-animation">✅ 🎉 ✅</p>', unsafe_allow_html=True)
                        st.success(f"🎉 Excellent work, Detective! Level {current} SOLVED!")

                        # Points: 100 base, bonus for first attempt
                        attempts = st.session_state['attempts'].get(current, 0) + 1
                        st.session_state['attempts'][current] = attempts
                        bonus = max(0, 100 - (attempts - 1) * 20)
                        st.session_state['points'] += bonus
                        st.session_state['streak'] += 1
                        st.session_state['completed_levels'].add(current)

                        st.info(f"🏅 +{bonus} points! (Attempt #{attempts})")

                        if st.session_state['streak'] >= 3:
                            st.success(f"🔥 {st.session_state['streak']}-level streak! You're on fire!")

                        if st.button("➡️ Next Case File"):
                            st.session_state['current_level'] = current + 1
                            st.rerun()
                    else:
                        attempts = st.session_state['attempts'].get(current, 0) + 1
                        st.session_state['attempts'][current] = attempts
                        st.session_state['streak'] = 0

                        # Provide helpful feedback based on the difference
                        if len(student_result) != len(expected_result):
                            st.warning(f"🤔 Close, but not quite! Your query returned {len(student_result)} rows, but we expected {len(expected_result)} rows. Check your WHERE conditions or JOINs.")
                        elif set(student_result.columns) != set(expected_result.columns):
                            st.warning(f"🤔 Almost there! Your columns don't match what we need. Expected columns: {list(expected_result.columns)}. Check your SELECT clause.")
                        else:
                            st.warning("🤔 The structure looks right, but the data doesn't match. Double-check your conditions and spelling.")

                        if attempts >= 3:
                            with st.expander("🆘 Show expected query (spoiler!)"):
                                st.code(level_data['check_query'], language='sql')

                except Exception as e:
                    st.error(f"❌ SQL Error: {e}")
                    st.info("💡 Check your syntax. Common issues: missing comma, wrong table name, or typo in column name.")
