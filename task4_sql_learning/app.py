"""
Task 4: SQL Learning Game — "Hogwarts School of SQL & Wizardry"
A Harry Potter-themed, immersive SQL learning platform where learners cast "SQL spells"
against a magical creatures database to progress through the classes.
"""
import streamlit as st
import sqlite3
import pandas as pd
import os
import random
import time
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "spellcraft.db")

# ============================================================
# Database Setup
# ============================================================
def init_db():
    """Create the wizard academy database with fantasy-themed tables."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS creatures (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL, species TEXT,
        element TEXT, power_level INTEGER, habitat TEXT,
        is_legendary BOOLEAN, discovered_by TEXT, discovery_year INTEGER
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS wizards (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL, house TEXT,
        specialty TEXT, rank TEXT, years_experience INTEGER, creatures_tamed INTEGER
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS spells (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL, element TEXT,
        difficulty TEXT, mana_cost INTEGER, damage INTEGER,
        wizard_id INTEGER, FOREIGN KEY (wizard_id) REFERENCES wizards(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS quests (
        id INTEGER PRIMARY KEY, title TEXT NOT NULL, difficulty TEXT,
        reward_gold INTEGER, creature_id INTEGER, wizard_id INTEGER,
        completed BOOLEAN,
        FOREIGN KEY (creature_id) REFERENCES creatures(id),
        FOREIGN KEY (wizard_id) REFERENCES wizards(id)
    )""")

    creatures = [
        (1,'Phoenix','Bird','Fire',95,'Volcanic Mountains',1,'Alaric',1205),
        (2,'Frost Wyrm','Dragon','Ice',88,'Frozen Peaks',1,'Seraphina',1342),
        (3,'Shadow Panther','Beast','Dark',72,'Dark Forest',0,'Theron',1501),
        (4,'Thunder Hawk','Bird','Lightning',65,'Storm Cliffs',0,'Elara',1623),
        (5,'Crystal Golem','Elemental','Earth',80,'Crystal Caves',0,'Borin',1189),
        (6,'Sea Serpent','Dragon','Water',91,'Deep Ocean',1,'Morgana',1067),
        (7,'Ember Fox','Beast','Fire',45,'Ashen Wastes',0,'Lyric',1720),
        (8,'Wind Sprite','Fairy','Air',38,'Sky Gardens',0,'Elara',1655),
        (9,'Iron Beetle','Insect','Earth',52,'Underground Mines',0,'Borin',1400),
        (10,'Storm Dragon','Dragon','Lightning',97,'Storm Cliffs',1,'Alaric',1100),
        (11,'Moss Turtle','Beast','Earth',35,'Enchanted Swamp',0,'Theron',1580),
        (12,'Lava Salamander','Reptile','Fire',60,'Volcanic Mountains',0,'Lyric',1690),
        (13,'Nightmare Stallion','Beast','Dark',78,'Shadow Realm',0,'Morgana',1455),
        (14,'Aurora Butterfly','Fairy','Light',42,'Sky Gardens',0,'Seraphina',1710),
        (15,'Abyssal Kraken','Beast','Water',93,'Deep Ocean',1,'Morgana',998),
    ]
    wizards = [
        (1,'Harry Potter','Gryffindor','Defense Against the Dark Arts','Auror',15,8),
        (2,'Draco Malfoy','Slytherin','Potions','Master',12,6),
        (3,'Severus Snape','Slytherin','Dark Arts','Professor',29,5),
        (4,'Hermione Granger','Gryffindor','Charms','Minister',15,4),
        (5,'Cedric Diggory','Hufflepuff','Transfiguration','Prefect',7,7),
        (6,'Luna Lovegood','Ravenclaw','Magizoology','Naturalist',14,9),
        (7,'Ron Weasley','Gryffindor','Herbology','Auror',15,3),
    ]
    spells = [
        (1,'Fireball','Fire','Advanced',50,85,1),
        (2,'Frost Nova','Ice','Intermediate',35,60,2),
        (3,'Shadow Bolt','Dark','Advanced',45,75,3),
        (4,'Gale Force','Air','Beginner',20,30,4),
        (5,'Earthquake','Earth','Advanced',55,90,5),
        (6,'Tidal Wave','Water','Expert',65,95,6),
        (7,'Ember Spark','Fire','Beginner',15,25,7),
        (8,'Blizzard','Ice','Expert',60,88,2),
        (9,'Dark Veil','Dark','Beginner',10,15,3),
        (10,'Stone Wall','Earth','Intermediate',30,0,5),
        (11,'Lightning Strike','Lightning','Advanced',50,82,1),
        (12,'Healing Rain','Water','Intermediate',40,0,6),
    ]
    quests = [
        (1,'Tame the Phoenix',  'Legendary',1000,1,1,1),
        (2,'Explore Frozen Peaks','Hard',500,2,2,1),
        (3,'Dark Forest Patrol','Medium',200,3,3,1),
        (4,'Storm Cliff Survey','Medium',250,4,4,0),
        (5,'Crystal Cave Expedition','Hard',600,5,5,0),
        (6,'Deep Sea Dive','Legendary',1200,6,6,1),
        (7,'Catch the Ember Fox','Easy',100,7,7,0),
        (8,'Sky Garden Harvest','Easy',80,8,4,1),
        (9,'Mine Exploration','Medium',300,9,5,0),
        (10,'Dragon Storm Hunt','Legendary',1500,10,1,0),
    ]

    c.execute("DELETE FROM creatures"); c.execute("DELETE FROM wizards")
    c.execute("DELETE FROM spells"); c.execute("DELETE FROM quests")
    c.executemany("INSERT INTO creatures VALUES (?,?,?,?,?,?,?,?,?)", creatures)
    c.executemany("INSERT INTO wizards VALUES (?,?,?,?,?,?,?)", wizards)
    c.executemany("INSERT INTO spells VALUES (?,?,?,?,?,?,?)", spells)
    c.executemany("INSERT INTO quests VALUES (?,?,?,?,?,?,?)", quests)
    conn.commit(); conn.close()

# ============================================================
# Levels
# ============================================================
LEVELS = [
    {
        "level": 1, "title": "📜 Scroll I: The Archive Spell — SELECT *",
        "concept": "SELECT basics", "xp": 100, "spell_name": "Reveal All",
        "story": "Welcome, young apprentice, to the Spellcraft Academy! Every wizard must learn to read the ancient archives. Your first spell will summon the full contents of a magical scroll. Cast the **Reveal All** incantation to see every creature recorded in our bestiary.",
        "challenge": "Retrieve ALL columns for ALL creatures from the `creatures` table.",
        "hint": "The incantation pattern is: `SELECT * FROM table_name`. The table holding our creatures is called `creatures`.",
        "sub_hint": "Try typing exactly: `SELECT * FROM creatures`",
        "check_query": "SELECT * FROM creatures",
        "validate": lambda r, e: len(r) == len(e) and len(r.columns) == len(e.columns),
    },
    {
        "level": 2, "title": "🔮 Scroll II: The Filter Charm — WHERE",
        "concept": "WHERE clause", "xp": 150, "spell_name": "Focus Lens",
        "story": "Excellent! But a true wizard doesn't summon *everything* — that's reckless. The **Focus Lens** spell lets you filter the archives and see only what matters. The Academy headmaster needs a list of all **legendary** creatures. These rare beings require special containment protocols.",
        "challenge": "Find all creatures where `is_legendary = 1`. Show their `name`, `species`, and `power_level`.",
        "hint": "Use `SELECT col1, col2 FROM table WHERE condition`. The column is `is_legendary` and legendary creatures have the value `1`.",
        "sub_hint": "Try: `SELECT name, species, power_level FROM creatures WHERE is_legendary = 1`",
        "check_query": "SELECT name, species, power_level FROM creatures WHERE is_legendary = 1",
        "validate": lambda r, e: len(r) == len(e),
    },
    {
        "level": 3, "title": "⚡ Scroll III: The Order Incantation — ORDER BY & LIMIT",
        "concept": "ORDER BY & LIMIT", "xp": 200, "spell_name": "Rank & Reveal",
        "story": "The Academy is preparing for the Tournament of Beasts! The headmaster needs the **top 5 most powerful creatures** to showcase as finalists. You must sort the bestiary by raw power and present only the elite.",
        "challenge": "Get `name` and `power_level` from `creatures`, ordered by `power_level` from highest to lowest, showing only the top 5.",
        "hint": "Use `ORDER BY column DESC` to sort from highest to lowest, and `LIMIT 5` to get only 5 rows.",
        "sub_hint": "Try: `SELECT name, power_level FROM creatures ORDER BY power_level DESC LIMIT 5`",
        "check_query": "SELECT name, power_level FROM creatures ORDER BY power_level DESC LIMIT 5",
        "validate": lambda r, e: len(r) == 5 and list(r.iloc[:, 1]) == list(e.iloc[:, 1]),
    },
    {
        "level": 4, "title": "📊 Scroll IV: The Aggregation Ritual — GROUP BY & COUNT",
        "concept": "GROUP BY & Aggregations", "xp": 250, "spell_name": "Census Pulse",
        "story": "The Creature Census is due! The Academy Council needs to know how many creatures belong to each element. Fire? Water? Dark? This knowledge is crucial for balancing the Academy's defense grid. Cast the **Census Pulse** to aggregate the data.",
        "challenge": "Count how many creatures belong to each `element`. Show the element and the count (name it `creature_count`). Order by count descending.",
        "hint": "Use `SELECT column, COUNT(*) as alias FROM table GROUP BY column ORDER BY alias DESC`.",
        "sub_hint": "Try: `SELECT element, COUNT(*) as creature_count FROM creatures GROUP BY element ORDER BY creature_count DESC`",
        "check_query": "SELECT element, COUNT(*) as creature_count FROM creatures GROUP BY element ORDER BY creature_count DESC",
        "validate": lambda r, e: len(r) == len(e) and 'creature_count' in [c.lower() for c in r.columns],
    },
    {
        "level": 5, "title": "🔗 Scroll V: The Binding Spell — JOIN",
        "concept": "JOIN operations", "xp": 300, "spell_name": "Soul Link",
        "story": "The most powerful spell in the wizard's arsenal is the **Soul Link** — the ability to connect separate scrolls of knowledge into one vision. The headmaster needs a report showing each quest alongside the creature it targets. Two scrolls, one truth.",
        "challenge": "JOIN `quests` with `creatures` (on `quests.creature_id = creatures.id`) to show the quest `title`, quest `difficulty`, and the creature's `name` (which you should label `creature_name`).",
        "hint": "Use `SELECT t1.col, t2.col as alias FROM t1 JOIN t2 ON t1.fk = t2.pk`. Connect `quests.creature_id` to `creatures.id`.",
        "sub_hint": "Try: `SELECT q.title, q.difficulty, c.name as creature_name FROM quests q JOIN creatures c ON q.creature_id = c.id`",
        "check_query": "SELECT q.title, q.difficulty, c.name as creature_name FROM quests q JOIN creatures c ON q.creature_id = c.id",
        "validate": lambda r, e: len(r) == len(e),
    },
    {
        "level": 6, "title": "🌟 Scroll VI: The Grand Synthesis — Complex Query",
        "concept": "Multi-table JOIN + GROUP BY", "xp": 400, "spell_name": "Omni-Vision",
        "story": "This is the final trial before you earn your wizard's staff. The Academy needs to know which wizard has been assigned the most quests. You must link the wizards table to the quests table, count each wizard's assigned quests, and rank them. Only the **Omni-Vision** spell can reveal this.",
        "challenge": "JOIN `quests` with `wizards` (on `quests.wizard_id = wizards.id`). Show wizard `name`, their `house`, and the count of quests as `quest_count`. Group by wizard name and order by quest_count descending.",
        "hint": "Combine JOIN + GROUP BY + ORDER BY. Link `quests.wizard_id` to `wizards.id`, group by `w.name`, count rows.",
        "sub_hint": "Try: `SELECT w.name, w.house, COUNT(*) as quest_count FROM quests q JOIN wizards w ON q.wizard_id = w.id GROUP BY w.name ORDER BY quest_count DESC`",
        "check_query": "SELECT w.name, w.house, COUNT(*) as quest_count FROM quests q JOIN wizards w ON q.wizard_id = w.id GROUP BY w.name ORDER BY quest_count DESC",
        "validate": lambda r, e: len(r) == len(e) and len(r) > 0,
    },
    {
        "level": 7, "title": "🏆 Final Trial: The Archmage Test — Subquery & HAVING",
        "concept": "Subqueries & HAVING", "xp": 500, "spell_name": "Archmage's Sight",
        "story": "You stand at the threshold of mastery. For your final trial, the Grand Council demands a truly advanced spell. Find every element that has an average power level above 70 — these are the 'Dominant Elements' that shape the balance of our world. Only a future Archmage can cast this.",
        "challenge": "Find elements where the AVERAGE `power_level` is greater than 70. Show the `element` and the average power (name it `avg_power`, rounded). Order by `avg_power` descending.",
        "hint": "Use `GROUP BY element` with `HAVING AVG(power_level) > 70`. Use `ROUND(AVG(...),1)` to round.",
        "sub_hint": "Try: `SELECT element, ROUND(AVG(power_level),1) as avg_power FROM creatures GROUP BY element HAVING avg_power > 70 ORDER BY avg_power DESC`",
        "check_query": "SELECT element, ROUND(AVG(power_level),1) as avg_power FROM creatures GROUP BY element HAVING avg_power > 70 ORDER BY avg_power DESC",
        "validate": lambda r, e: len(r) == len(e) and len(r) > 0,
    },
]

RANKS = [
    (0, "Novice Apprentice", "🧹"), (200, "Spell Scribe", "📜"),
    (500, "Junior Wizard", "🪄"), (900, "Enchanter", "✨"),
    (1400, "Grand Wizard", "🧙"), (1900, "Archmage", "👑"),
]

def get_rank(xp):
    rank = RANKS[0]
    for threshold, name, icon in RANKS:
        if xp >= threshold:
            rank = (threshold, name, icon)
    return rank

def get_next_rank(xp):
    for threshold, name, icon in RANKS:
        if xp < threshold:
            return (threshold, name, icon)
    return None

# ============================================================
# Streamlit App
# ============================================================
st.set_page_config(page_title="Hogwarts SQL Academy", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Inter:wght@400;600&display=swap');
.main-title {
    font-family: 'Cinzel', serif; font-size: 2.6rem; font-weight: 700;
    background: linear-gradient(90deg, #ffd700, #ff8c00, #ffd700);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    text-align: center; text-shadow: 0 0 30px rgba(255,215,0,0.3);
}
.subtitle { text-align:center; color:#a08050; font-size:1.1rem; font-family:'Cinzel',serif; margin-bottom:1.5rem; }
.story-box {
    background: linear-gradient(135deg, #1a0a2e 0%, #16213e 100%);
    border-left: 5px solid #9b59b6; padding: 1.5rem; border-radius: 0 12px 12px 0;
    margin: 1rem 0; color: #e8d5f5 !important; font-size: 1.05rem; line-height: 1.8;
}
.challenge-box {
    background: linear-gradient(135deg, #2a1a00 0%, #1a1200 100%);
    border: 2px solid #ffd700; padding: 1.5rem; border-radius: 12px;
    margin: 1rem 0; color: #fff5cc !important; font-size: 1.05rem; line-height: 1.7;
}
.hint-box {
    background: #0d1a2e; border-left: 5px solid #3498db; padding: 1rem;
    border-radius: 0 10px 10px 0; color: #a8d8ea !important; font-size: 1rem;
}
.xp-bar-outer {
    background: #1a1a2e; border-radius: 10px; height: 22px; width: 100%;
    overflow: hidden; border: 1px solid #333;
}
.xp-bar-inner {
    height: 100%; border-radius: 10px;
    background: linear-gradient(90deg, #ffd700, #ff8c00);
    transition: width 0.5s ease;
}
.rank-display {
    text-align: center; padding: 0.8rem; border-radius: 10px;
    background: linear-gradient(135deg, #1a0a2e, #0d1117);
    border: 1px solid #ffd70055; margin-bottom: 1rem;
}
.spell-cast {
    font-size: 2.5rem; text-align: center;
    animation: castPulse 0.8s ease-in-out;
}
@keyframes castPulse {
    0% { transform: scale(0.5); opacity: 0; }
    50% { transform: scale(1.3); opacity: 1; }
    100% { transform: scale(1); opacity: 1; }
}
.badge { display:inline-block; padding:4px 12px; border-radius:20px; font-weight:bold; margin:3px; font-size:0.85rem; }
.badge-done { background:#1a3a1a; color:#4ECDC4; border:1px solid #4ECDC455; }
.badge-current { background:#3a2a0a; color:#FFD700; border:1px solid #FFD70055; }
.badge-locked { background:#1a1a1a; color:#555; border:1px solid #33333355; }
.schema-card {
    background: linear-gradient(135deg, #0d1117, #161b22); border: 1px solid #30363d;
    border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;
}
.schema-card h4 {
    color: #ffd700 !important;
    margin-top: 0;
}
.schema-card pre {
    color: #a8d8ea !important;
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    font-size: 0.85rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown('''<div style="display: flex; align-items: center; justify-content: center; gap: 15px;">
    <span style="font-size: 2.2rem;">🦁🐍</span>
    <p class="main-title" style="margin:0;">Hogwarts School of SQL & Wizardry</p>
    <span style="font-size: 2.2rem;">🦅🦡</span>
</div>''', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Master the ancient art of SQL — one spell at a time ⚡</p>', unsafe_allow_html=True)

# Initialize
init_db()

if 'completed_levels' not in st.session_state: st.session_state['completed_levels'] = set()
if 'current_level' not in st.session_state: st.session_state['current_level'] = 1
if 'attempts' not in st.session_state: st.session_state['attempts'] = {}
if 'xp' not in st.session_state: st.session_state['xp'] = 0
if 'streak' not in st.session_state: st.session_state['streak'] = 0
if 'spells_unlocked' not in st.session_state: st.session_state['spells_unlocked'] = []
if 'show_sub_hint' not in st.session_state: st.session_state['show_sub_hint'] = {}

# ============================================================
# Sidebar — Wizard Profile
# ============================================================
xp = st.session_state['xp']
rank_info = get_rank(xp)
next_rank = get_next_rank(xp)

st.sidebar.markdown(f"""<div class="rank-display">
<div style="font-size:2rem;">{rank_info[2]}</div>
<div style="font-size:1.1rem; font-weight:bold; color:#ffd700;">{rank_info[1]}</div>
<div style="color:#888; font-size:0.85rem; margin-top:4px;">XP: {xp}</div>
</div>""", unsafe_allow_html=True)

if next_rank:
    progress_pct = ((xp - rank_info[0]) / (next_rank[0] - rank_info[0])) * 100
    st.sidebar.markdown(f"<div style='font-size:0.8rem;color:#888;margin-bottom:4px;'>Next: {next_rank[2]} {next_rank[1]} ({next_rank[0]} XP)</div>", unsafe_allow_html=True)
    st.sidebar.markdown(f'<div class="xp-bar-outer"><div class="xp-bar-inner" style="width:{progress_pct:.0f}%"></div></div>', unsafe_allow_html=True)

st.sidebar.markdown(f"<div style='text-align:center; margin-top:8px;'>🔥 Streak: **{st.session_state['streak']}**</div>", unsafe_allow_html=True)
st.sidebar.divider()

st.sidebar.subheader("📋 Spell Scrolls")
for lv in LEVELS:
    n = lv['level']
    if n in st.session_state['completed_levels']:
        st.sidebar.markdown(f"<span class='badge badge-done'>✅ {n}</span> {lv['concept']}", unsafe_allow_html=True)
    elif n == st.session_state['current_level']:
        st.sidebar.markdown(f"<span class='badge badge-current'>🔓 {n}</span> {lv['concept']}", unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"<span class='badge badge-locked'>🔒 {n}</span> {lv['concept']}", unsafe_allow_html=True)

nav = st.sidebar.radio("Navigate", ["🎮 Spell Trials", "📚 Grimoire (Schema)", "🏆 Trophy Room", "🧪 Sandbox"], label_visibility="collapsed")

# ============================================================
# Grimoire (Schema)
# ============================================================
if nav == "📚 Grimoire (Schema)":
    st.header("📚 The Grimoire — Database Schema")
    st.markdown("Study these ancient scrolls before casting your spells:")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🐉 creatures")
        st.code("""id              INTEGER  PRIMARY KEY
name            TEXT     creature name
species         TEXT     Bird/Dragon/Beast/...
element         TEXT     Fire/Ice/Water/...
power_level     INTEGER  strength rating
habitat         TEXT     where it lives
is_legendary    BOOLEAN  0 or 1
discovered_by   TEXT     wizard who found it
discovery_year  INTEGER  year discovered""")

        st.subheader("✨ spells")
        st.code("""id          INTEGER  PRIMARY KEY
name        TEXT     spell name
element     TEXT     Fire/Ice/Water/...
difficulty  TEXT     Beginner-Expert
mana_cost   INTEGER  mana needed
damage      INTEGER  damage dealt
wizard_id   INTEGER  FK → wizards.id""")

    with col2:
        st.subheader("🧙 wizards")
        st.code("""id                INTEGER  PRIMARY KEY
name              TEXT     wizard name
house             TEXT     Hogwarts house (Gryffindor/Slytherin/...)
specialty         TEXT     magic type
rank              TEXT     Apprentice / Auror / Professor
years_experience  INTEGER  years practicing
creatures_tamed   INTEGER  creature count""")

        st.subheader("⚔️ quests")
        st.code("""id           INTEGER  PRIMARY KEY
title        TEXT     quest name
difficulty   TEXT     Easy / Medium / Hard / Legendary
reward_gold  INTEGER  gold reward
creature_id  INTEGER  FK → creatures.id
wizard_id    INTEGER  FK → wizards.id
completed    BOOLEAN  0 or 1""")

    st.divider()
    st.subheader("🔎 Data Preview")
    conn = sqlite3.connect(DB_PATH)
    for tbl in ['creatures', 'wizards', 'spells', 'quests']:
        with st.expander(f"Preview: {tbl}"):
            st.dataframe(pd.read_sql_query(f"SELECT * FROM {tbl}", conn), use_container_width=True)
    conn.close()

# ============================================================
# Trophy Room
# ============================================================
elif nav == "🏆 Trophy Room":
    st.header("🏆 Trophy Room")
    comp = st.session_state['completed_levels']
    trophies = [
        ("🧹 Apprentice Initiate", "Complete Scroll I", 1 in comp),
        ("🔮 Filter Adept", "Complete Scroll II", 2 in comp),
        ("⚡ Sorter Supreme", "Complete Scroll III", 3 in comp),
        ("📊 Census Master", "Complete Scroll IV", 4 in comp),
        ("🔗 Soul Linker", "Complete Scroll V (JOIN)", 5 in comp),
        ("🌟 Grand Synthesizer", "Complete Scroll VI", 6 in comp),
        ("👑 Archmage", "Complete the Final Trial", 7 in comp),
        ("🔥 Blazing Streak", "Get a 3+ streak", st.session_state['streak'] >= 3),
        ("💎 XP Hoarder", "Earn 1000+ XP", xp >= 1000),
        ("🏅 Curriculum Complete", "Finish all 7 scrolls", len(comp) == 7),
    ]
    cols = st.columns(2)
    for i, (name, desc, earned) in enumerate(trophies):
        with cols[i % 2]:
            if earned:
                st.success(f"{name} — {desc} ✅")
            else:
                st.info(f"{name} — {desc} 🔒")

    if st.session_state['spells_unlocked']:
        st.divider()
        st.subheader("🪄 Spells Unlocked")
        for sp in st.session_state['spells_unlocked']:
            st.markdown(f"✨ **{sp}**")

# ============================================================
# Sandbox
# ============================================================
elif nav == "🧪 Sandbox":
    st.header("🧪 Spell Sandbox — Free Practice")
    st.markdown("Cast any SQL spell against the academy database. No rules, no scoring — just pure experimentation.")
    sandbox_query = st.text_area("Write your SQL spell:", height=150, placeholder="SELECT * FROM creatures WHERE element = 'Fire'")
    if st.button("🪄 Cast Spell", type="primary") and sandbox_query:
        if not sandbox_query.strip().upper().startswith("SELECT"):
            st.error("⚠️ Only SELECT spells are allowed — wizards observe, they don't alter the archives!")
        else:
            try:
                conn = sqlite3.connect(DB_PATH)
                result = pd.read_sql_query(sandbox_query, conn)
                conn.close()
                st.dataframe(result, use_container_width=True)
                st.caption(f"Returned {len(result)} rows × {len(result.columns)} columns")
            except Exception as e:
                st.error(f"❌ Spell failed: {e}")

# ============================================================
# Play Mode — Spell Trials
# ============================================================
else:
    current = st.session_state['current_level']
    level_data = None
    for lv in LEVELS:
        if lv['level'] == current:
            level_data = lv
            break

    if level_data is None:
        st.markdown('<p class="spell-cast">🎓🏆🎓</p>', unsafe_allow_html=True)
        st.success("🎓 You have graduated from Hogwarts! You are now a fully certified Auror!")
        st.balloons()
        st.markdown(f"**Final XP:** {st.session_state['xp']}")
        st.markdown(f"**Rank:** {get_rank(st.session_state['xp'])[2]} {get_rank(st.session_state['xp'])[1]}")
        st.markdown(f"**Scrolls Completed:** {len(st.session_state['completed_levels'])}/{len(LEVELS)}")
        if st.button("🔄 Restart Academy"):
            for k in ['current_level','completed_levels','xp','streak','attempts','spells_unlocked','show_sub_hint']:
                if k in st.session_state: del st.session_state[k]
            st.rerun()
    else:
        st.markdown(f"## {level_data['title']}")
        st.markdown(f"<div style='color:#888;'>Spell: <b style=\"color:#ffd700\">{level_data['spell_name']}</b> | Reward: <b style=\"color:#4ECDC4\">+{level_data['xp']} XP</b></div>", unsafe_allow_html=True)

        st.markdown(f'<div class="story-box">📖 {level_data["story"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="challenge-box">🎯 <strong>Your Mission:</strong> {level_data["challenge"]}</div>', unsafe_allow_html=True)

        with st.expander("💡 Need a hint?"):
            st.markdown(f'<div class="hint-box">{level_data["hint"]}</div>', unsafe_allow_html=True)

        # Adaptive: show easier sub-hint after 2+ failed attempts
        attempts_so_far = st.session_state['attempts'].get(current, 0)
        if attempts_so_far >= 2:
            with st.expander("🆘 Struggling? Here's a bigger hint"):
                st.markdown(f'<div class="hint-box">💡 <b>Step-by-step:</b> {level_data["sub_hint"]}</div>', unsafe_allow_html=True)

        # Show relevant table preview
        with st.expander("👀 Peek at the data"):
            conn = sqlite3.connect(DB_PATH)
            if current <= 4:
                st.caption("creatures table:")
                st.dataframe(pd.read_sql_query("SELECT * FROM creatures LIMIT 5", conn), use_container_width=True)
            elif current == 5:
                st.caption("quests table:"); st.dataframe(pd.read_sql_query("SELECT * FROM quests LIMIT 5", conn), use_container_width=True)
                st.caption("creatures table:"); st.dataframe(pd.read_sql_query("SELECT * FROM creatures LIMIT 5", conn), use_container_width=True)
            else:
                for t in ['quests','wizards','creatures']:
                    st.caption(f"{t} table:"); st.dataframe(pd.read_sql_query(f"SELECT * FROM {t} LIMIT 4", conn), use_container_width=True)
            conn.close()

        query_input = st.text_area("🪄 Write your SQL spell:", height=130, key=f"q_{current}", placeholder="SELECT ... FROM ...")

        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            run_btn = st.button("⚡ Cast Spell", type="primary")
        with col2:
            skip_btn = st.button("⏭️ Skip Scroll")

        if skip_btn:
            st.session_state['current_level'] = current + 1
            st.session_state['streak'] = 0
            st.rerun()

        if run_btn and query_input:
            if not query_input.strip().upper().startswith("SELECT"):
                st.error("⚠️ Only SELECT incantations are permitted! Wizards observe, never tamper.")
            else:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    student_result = pd.read_sql_query(query_input, conn)
                    expected_result = pd.read_sql_query(level_data['check_query'], conn)
                    conn.close()

                    st.subheader("📋 Spell Result:")
                    st.dataframe(student_result, use_container_width=True)

                    is_correct = False
                    try: is_correct = level_data['validate'](student_result, expected_result)
                    except: is_correct = len(student_result) == len(expected_result)

                    if is_correct:
                        st.markdown('<p class="spell-cast">✨🪄✨</p>', unsafe_allow_html=True)
                        st.success(f"🎉 Spell mastered! You have unlocked **{level_data['spell_name']}**!")

                        # Only award XP if not already completed
                        if current not in st.session_state['completed_levels']:
                            attempts_count = st.session_state['attempts'].get(current, 0) + 1
                            st.session_state['attempts'][current] = attempts_count
                            bonus = max(0, level_data['xp'] - (attempts_count - 1) * 30)
                            st.session_state['xp'] += bonus
                            st.session_state['streak'] += 1
                            st.session_state['completed_levels'].add(current)
                            st.session_state['spells_unlocked'].append(level_data['spell_name'])
                            st.info(f"🏅 +{bonus} XP earned! (Attempt #{attempts_count})")
                            if st.session_state['streak'] >= 3:
                                st.success(f"🔥 {st.session_state['streak']}-scroll streak! Your wand is ablaze!")

                        # Auto-advance: set next level and provide a rerun button
                        st.session_state['current_level'] = current + 1
                        st.button("➡️ Next Scroll", on_click=lambda: None)  # Just triggers rerun
                    else:
                        attempts_count = st.session_state['attempts'].get(current, 0) + 1
                        st.session_state['attempts'][current] = attempts_count
                        st.session_state['streak'] = 0

                        if len(student_result) != len(expected_result):
                            st.warning(f"🔮 Your spell summoned {len(student_result)} rows, but the correct incantation yields {len(expected_result)}. Check your WHERE conditions or JOINs.")
                        elif set(student_result.columns) != set(expected_result.columns):
                            exp_cols = list(expected_result.columns)
                            st.warning(f"🔮 Wrong columns! Expected: `{exp_cols}`. Check your SELECT clause.")
                        else:
                            st.warning("🔮 The structure looks correct but the values don't match. Double-check your conditions and spelling.")

                        if attempts_count >= 3:
                            with st.expander("🆘 Reveal the correct incantation (spoiler)"):
                                st.code(level_data['check_query'], language='sql')

                except Exception as e:
                    st.error(f"❌ Spell misfired: {e}")
                    st.info("💡 Common issues: missing comma, wrong table name, or a typo in a column name.")
