"""
Task 3: Pokemon Battle Arena
Interactive Streamlit battle game with SQLite, cheat codes, and analysis.
"""
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import random
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "pokemon.db")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Pokemon.csv")

# Type effectiveness chart (simplified)
TYPE_CHART = {
    'Fire': {'Grass': 2.0, 'Water': 0.5, 'Ice': 2.0, 'Bug': 2.0, 'Steel': 2.0, 'Fire': 0.5, 'Rock': 0.5, 'Dragon': 0.5},
    'Water': {'Fire': 2.0, 'Ground': 2.0, 'Rock': 2.0, 'Water': 0.5, 'Grass': 0.5, 'Dragon': 0.5},
    'Grass': {'Water': 2.0, 'Ground': 2.0, 'Rock': 2.0, 'Fire': 0.5, 'Grass': 0.5, 'Poison': 0.5, 'Flying': 0.5, 'Bug': 0.5, 'Dragon': 0.5, 'Steel': 0.5},
    'Electric': {'Water': 2.0, 'Flying': 2.0, 'Electric': 0.5, 'Grass': 0.5, 'Ground': 0.0, 'Dragon': 0.5},
    'Ice': {'Grass': 2.0, 'Ground': 2.0, 'Flying': 2.0, 'Dragon': 2.0, 'Fire': 0.5, 'Water': 0.5, 'Ice': 0.5, 'Steel': 0.5},
    'Fighting': {'Normal': 2.0, 'Ice': 2.0, 'Rock': 2.0, 'Dark': 2.0, 'Steel': 2.0, 'Poison': 0.5, 'Flying': 0.5, 'Psychic': 0.5, 'Bug': 0.5, 'Fairy': 0.5, 'Ghost': 0.0},
    'Poison': {'Grass': 2.0, 'Fairy': 2.0, 'Poison': 0.5, 'Ground': 0.5, 'Rock': 0.5, 'Ghost': 0.5, 'Steel': 0.0},
    'Ground': {'Fire': 2.0, 'Electric': 2.0, 'Poison': 2.0, 'Rock': 2.0, 'Steel': 2.0, 'Grass': 0.5, 'Bug': 0.5, 'Flying': 0.0},
    'Flying': {'Grass': 2.0, 'Fighting': 2.0, 'Bug': 2.0, 'Electric': 0.5, 'Rock': 0.5, 'Steel': 0.5},
    'Psychic': {'Fighting': 2.0, 'Poison': 2.0, 'Psychic': 0.5, 'Steel': 0.5, 'Dark': 0.0},
    'Bug': {'Grass': 2.0, 'Psychic': 2.0, 'Dark': 2.0, 'Fire': 0.5, 'Fighting': 0.5, 'Poison': 0.5, 'Flying': 0.5, 'Ghost': 0.5, 'Steel': 0.5, 'Fairy': 0.5},
    'Rock': {'Fire': 2.0, 'Ice': 2.0, 'Flying': 2.0, 'Bug': 2.0, 'Fighting': 0.5, 'Ground': 0.5, 'Steel': 0.5},
    'Ghost': {'Psychic': 2.0, 'Ghost': 2.0, 'Dark': 0.5, 'Normal': 0.0},
    'Dragon': {'Dragon': 2.0, 'Steel': 0.5, 'Fairy': 0.0},
    'Dark': {'Psychic': 2.0, 'Ghost': 2.0, 'Fighting': 0.5, 'Dark': 0.5, 'Fairy': 0.5},
    'Steel': {'Ice': 2.0, 'Rock': 2.0, 'Fairy': 2.0, 'Fire': 0.5, 'Water': 0.5, 'Electric': 0.5, 'Steel': 0.5},
    'Fairy': {'Fighting': 2.0, 'Dragon': 2.0, 'Dark': 2.0, 'Fire': 0.5, 'Poison': 0.5, 'Steel': 0.5},
    'Normal': {'Rock': 0.5, 'Steel': 0.5, 'Ghost': 0.0},
}


def init_db():
    """Load Pokemon CSV into SQLite with type effectiveness table."""
    if os.path.exists(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Main pokemon table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pokemon (
            pokedex_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type1 TEXT,
            type2 TEXT,
            total INTEGER,
            hp INTEGER,
            attack INTEGER,
            defense INTEGER,
            sp_atk INTEGER,
            sp_def INTEGER,
            speed INTEGER,
            generation INTEGER,
            legendary BOOLEAN
        )
    """)

    # Type effectiveness table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS type_effectiveness (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attack_type TEXT NOT NULL,
            defend_type TEXT NOT NULL,
            multiplier REAL NOT NULL
        )
    """)

    # Battle history log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS battle_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1_pokemon TEXT,
            player2_pokemon TEXT,
            winner TEXT,
            total_turns INTEGER,
            cheats_used TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Load Pokemon data
    df = pd.read_csv(DATA_PATH)
    for _, row in df.iterrows():
        legendary = str(row['Legendary']).strip().lower() in ['true', '1']
        cursor.execute("""
            INSERT OR REPLACE INTO pokemon VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(row['#']), row['Name'],
            row['Type 1'], row['Type 2'] if pd.notna(row['Type 2']) else None,
            int(row['Total']), int(row['HP']), int(row['Attack']),
            int(row['Defense']), int(row['Sp. Atk']), int(row['Sp. Def']),
            int(row['Speed']), int(row['Generation']), legendary
        ))

    # Load type effectiveness
    for atk_type, matchups in TYPE_CHART.items():
        for def_type, mult in matchups.items():
            cursor.execute("INSERT INTO type_effectiveness (attack_type, defend_type, multiplier) VALUES (?, ?, ?)",
                           (atk_type, def_type, mult))

    conn.commit()
    conn.close()


def get_conn():
    return sqlite3.connect(DB_PATH)


def get_pokemon_list():
    conn = get_conn()
    df = pd.read_sql_query("SELECT name FROM pokemon ORDER BY name", conn)
    conn.close()
    return df['name'].tolist()


def get_pokemon_stats(name):
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM pokemon WHERE name = ?", conn, params=[name])
    conn.close()
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def get_type_multiplier(atk_type, def_type1, def_type2=None):
    conn = get_conn()
    mult = 1.0
    row = pd.read_sql_query(
        "SELECT multiplier FROM type_effectiveness WHERE attack_type = ? AND defend_type = ?",
        conn, params=[atk_type, def_type1])
    if not row.empty:
        mult *= row.iloc[0]['multiplier']
    if def_type2:
        row2 = pd.read_sql_query(
            "SELECT multiplier FROM type_effectiveness WHERE attack_type = ? AND defend_type = ?",
            conn, params=[atk_type, def_type2])
        if not row2.empty:
            mult *= row2.iloc[0]['multiplier']
    conn.close()
    return mult


def calculate_damage(attacker, defender):
    """
    Damage formula:
    Base damage = (attacker.Attack * 2 / defender.Defense) * type_multiplier + random(1,10)
    We use Attack vs Defense for physical, and pick the higher of Attack/Sp.Atk for the attacker.
    """
    atk_stat = max(attacker['attack'], attacker['sp_atk'])
    def_stat = max(defender['defense'], defender['sp_def'])

    type_mult = get_type_multiplier(attacker['type1'], defender['type1'], defender['type2'])

    base_damage = max(1, int((atk_stat * 2 / max(1, def_stat)) * type_mult * 10 + random.randint(1, 10)))
    return base_damage, type_mult


# ============================================================
# Streamlit App
# ============================================================
st.set_page_config(page_title="Pokemon Battle Arena", page_icon="⚔️", layout="wide")

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #FF0000, #CC0000, #FF4444);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    .pokemon-card {
        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a2e 100%);
        border-radius: 15px;
        padding: 1rem;
        border: 2px solid #FFD700;
    }
    .battle-log {
        background: #0d1117;
        border-radius: 10px;
        padding: 1rem;
        font-family: monospace;
        max-height: 400px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">⚔️ Pokémon Battle Arena</p>', unsafe_allow_html=True)

init_db()

tab = st.sidebar.radio("Navigate", [
    "⚔️ Battle Arena",
    "🔑 Cheat Codes",
    "📊 Pokemon Insights"
])

# ============================================================
# Task 3.2: Battle Arena
# ============================================================
if tab == "⚔️ Battle Arena":
    st.header("⚔️ Battle Arena")

    pokemon_list = get_pokemon_list()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔴 Player 1")
        p1_pokemon = st.multiselect("Select 1-3 Pokemon:", pokemon_list, key="p1",
                                     max_selections=3, default=[pokemon_list[0]] if pokemon_list else [])
    with col2:
        st.subheader("🔵 Player 2 (AI)")
        p2_mode = st.radio("Opponent:", ["Random AI", "Choose Pokemon"])
        if p2_mode == "Random AI":
            if st.button("🎲 Randomize AI Team"):
                st.session_state['ai_team'] = random.sample(pokemon_list, min(3, len(p1_pokemon) if p1_pokemon else 1))
            p2_pokemon = st.session_state.get('ai_team', random.sample(pokemon_list, min(3, len(p1_pokemon) if p1_pokemon else 1)))
            st.write("AI Team:", ", ".join(p2_pokemon))
        else:
            p2_pokemon = st.multiselect("Select 1-3 Pokemon:", pokemon_list, key="p2",
                                         max_selections=3)

    # Show selected Pokemon stats
    if p1_pokemon:
        st.divider()
        cols = st.columns(len(p1_pokemon))
        for i, name in enumerate(p1_pokemon):
            stats = get_pokemon_stats(name)
            if stats:
                with cols[i]:
                    st.markdown(f"### 🔴 {name}")
                    st.markdown(f"**Type:** {stats['type1']}" + (f" / {stats['type2']}" if stats['type2'] else ""))
                    st.markdown(f"HP: {stats['hp']} | ATK: {stats['attack']} | DEF: {stats['defense']}")
                    st.markdown(f"Sp.ATK: {stats['sp_atk']} | Sp.DEF: {stats['sp_def']} | SPD: {stats['speed']}")

    # Battle simulation
    if p1_pokemon and p2_pokemon and st.button("⚔️ START BATTLE!", type="primary"):
        battle_log = []
        cheats_used = st.session_state.get('cheats_applied', [])

        # Create HP trackers (make copies at battle start)
        p1_team = []
        for name in p1_pokemon:
            stats = get_pokemon_stats(name)
            if stats:
                stats['current_hp'] = stats['hp']
                p1_team.append(stats)

        p2_team = []
        for name in p2_pokemon:
            stats = get_pokemon_stats(name)
            if stats:
                stats['current_hp'] = stats['hp']
                p2_team.append(stats)

        p1_idx, p2_idx = 0, 0
        turn = 0

        battle_container = st.container()

        while p1_idx < len(p1_team) and p2_idx < len(p2_team):
            turn += 1
            attacker1 = p1_team[p1_idx]
            attacker2 = p2_team[p2_idx]

            # Speed determines who goes first
            if attacker1['speed'] >= attacker2['speed']:
                first, second = attacker1, attacker2
                first_label, second_label = "🔴 P1", "🔵 P2"
            else:
                first, second = attacker2, attacker1
                first_label, second_label = "🔵 P2", "🔴 P1"

            # First attack
            dmg, mult = calculate_damage(first, second)
            second['current_hp'] -= dmg
            effect_text = ""
            if mult > 1.5:
                effect_text = " ⚡ Super effective!"
            elif mult < 0.8 and mult > 0:
                effect_text = " 🛡️ Not very effective..."
            elif mult == 0:
                effect_text = " ❌ No effect!"
                dmg = 0

            battle_log.append(f"Turn {turn}: {first_label} {first['name']} attacks {second['name']} for {dmg} damage!{effect_text}")

            if second['current_hp'] <= 0:
                battle_log.append(f"💀 {second['name']} fainted!")
                if second == p1_team[p1_idx]:
                    p1_idx += 1
                    if p1_idx < len(p1_team):
                        battle_log.append(f"🔴 P1 sends out {p1_team[p1_idx]['name']}!")
                else:
                    p2_idx += 1
                    if p2_idx < len(p2_team):
                        battle_log.append(f"🔵 P2 sends out {p2_team[p2_idx]['name']}!")
                continue

            # Second attack
            dmg2, mult2 = calculate_damage(second, first)
            first['current_hp'] -= dmg2
            effect_text2 = ""
            if mult2 > 1.5:
                effect_text2 = " ⚡ Super effective!"
            elif mult2 < 0.8 and mult2 > 0:
                effect_text2 = " 🛡️ Not very effective..."
            elif mult2 == 0:
                effect_text2 = " ❌ No effect!"
                dmg2 = 0

            battle_log.append(f"Turn {turn}: {second_label} {second['name']} attacks {first['name']} for {dmg2} damage!{effect_text2}")

            if first['current_hp'] <= 0:
                battle_log.append(f"💀 {first['name']} fainted!")
                if first == p1_team[p1_idx]:
                    p1_idx += 1
                    if p1_idx < len(p1_team):
                        battle_log.append(f"🔴 P1 sends out {p1_team[p1_idx]['name']}!")
                else:
                    p2_idx += 1
                    if p2_idx < len(p2_team):
                        battle_log.append(f"🔵 P2 sends out {p2_team[p2_idx]['name']}!")

            if turn > 100:
                battle_log.append("⏰ Battle timed out after 100 turns!")
                break

        # Determine winner
        if p1_idx >= len(p1_team):
            winner = "🔵 Player 2 (AI) Wins!"
            winner_name = "P2"
        elif p2_idx >= len(p2_team):
            winner = "🔴 Player 1 Wins!"
            winner_name = "P1"
        else:
            winner = "🤝 Draw!"
            winner_name = "Draw"

        # Log battle to database
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO battle_log (player1_pokemon, player2_pokemon, winner, total_turns, cheats_used)
            VALUES (?, ?, ?, ?, ?)
        """, (
            ", ".join(p1_pokemon),
            ", ".join(p2_pokemon),
            winner_name,
            turn,
            ", ".join(cheats_used) if cheats_used else "None"
        ))
        conn.commit()
        conn.close()

        # Display results
        with battle_container:
            st.markdown(f"## {winner}")
            st.markdown(f"**Total turns:** {turn}")

            st.subheader("📜 Battle Log")
            log_text = "\n".join(battle_log)
            st.code(log_text)

# ============================================================
# Task 3.3: Cheat Codes
# ============================================================
elif tab == "🔑 Cheat Codes":
    st.header("🔑 Cheat Codes")
    st.markdown("Enter a cheat code to modify the database and get an unfair advantage!")

    if 'cheats_applied' not in st.session_state:
        st.session_state['cheats_applied'] = []

    pokemon_list = get_pokemon_list()
    target_pokemon = st.selectbox("Select your Pokemon to apply cheat to:", pokemon_list)

    cheat_code = st.text_input("Enter cheat code:").strip().upper()

    cheat_descriptions = {
        "UPUPDOWNDOWN": "🔋 Doubles your Pokemon's HP",
        "GODMODE": "🛡️ Sets Defense and Sp.Def to 999",
        "LEGENDARY": "⭐ Inserts a custom overpowered Pokemon (MewThree)",
        "NERF": "📉 Reduces all opponent-type Pokemon stats by 50%",
        "MAXPOWER": "💪 Sets Attack and Sp.Atk to 999"
    }

    st.markdown("### Available Cheat Codes:")
    for code, desc in cheat_descriptions.items():
        st.markdown(f"- `{code}`: {desc}")

    if st.button("🔓 Apply Cheat!", type="primary"):
        conn = get_conn()
        cursor = conn.cursor()

        if cheat_code == "UPUPDOWNDOWN":
            cursor.execute("UPDATE pokemon SET hp = hp * 2 WHERE name = ?", (target_pokemon,))
            conn.commit()
            new_hp = pd.read_sql_query("SELECT hp FROM pokemon WHERE name = ?", conn, params=[target_pokemon])
            st.success(f"✅ CHEAT ACTIVATED! {target_pokemon}'s HP doubled to {new_hp.iloc[0]['hp']}!")
            st.session_state['cheats_applied'].append(f"UPUPDOWNDOWN on {target_pokemon}")

        elif cheat_code == "GODMODE":
            cursor.execute("UPDATE pokemon SET defense = 999, sp_def = 999 WHERE name = ?", (target_pokemon,))
            conn.commit()
            st.success(f"✅ CHEAT ACTIVATED! {target_pokemon}'s Defense and Sp.Def set to 999!")
            st.session_state['cheats_applied'].append(f"GODMODE on {target_pokemon}")

        elif cheat_code == "LEGENDARY":
            cursor.execute("""
                INSERT OR REPLACE INTO pokemon VALUES
                (9999, 'MewThree', 'Psychic', 'Dragon', 999, 500, 500, 500, 500, 500, 500, 99, 1)
            """)
            conn.commit()
            st.success("✅ CHEAT ACTIVATED! MewThree has been added to the database!")
            st.session_state['cheats_applied'].append("LEGENDARY (MewThree)")

        elif cheat_code == "NERF":
            # Get the target pokemon's type, nerf all Pokemon of opposite type
            target_stats = get_pokemon_stats(target_pokemon)
            if target_stats:
                cursor.execute("""
                    UPDATE pokemon SET attack = attack / 2, defense = defense / 2,
                           sp_atk = sp_atk / 2, sp_def = sp_def / 2, speed = speed / 2
                    WHERE name != ?
                """, (target_pokemon,))
                conn.commit()
                st.success(f"✅ CHEAT ACTIVATED! All other Pokemon stats reduced by 50%!")
                st.session_state['cheats_applied'].append(f"NERF (all except {target_pokemon})")

        elif cheat_code == "MAXPOWER":
            cursor.execute("UPDATE pokemon SET attack = 999, sp_atk = 999 WHERE name = ?", (target_pokemon,))
            conn.commit()
            st.success(f"✅ CHEAT ACTIVATED! {target_pokemon}'s Attack and Sp.Atk set to 999!")
            st.session_state['cheats_applied'].append(f"MAXPOWER on {target_pokemon}")

        else:
            st.error("❌ Invalid cheat code! Try one of the codes listed above.")

        conn.close()

    # Cheat Audit
    st.divider()
    st.subheader("🔍 Cheat Audit")
    if st.button("Run Cheat Audit"):
        conn = get_conn()
        # Detect cheats: Pokemon with stats exceeding natural maximums
        audit = pd.read_sql_query("""
            SELECT name, hp, attack, defense, sp_atk, sp_def, speed, total,
                   CASE WHEN hp > 255 THEN 'SUSPICIOUS HP' ELSE 'OK' END as hp_check,
                   CASE WHEN attack > 190 THEN 'SUSPICIOUS ATK' ELSE 'OK' END as atk_check,
                   CASE WHEN defense > 230 THEN 'SUSPICIOUS DEF' ELSE 'OK' END as def_check,
                   CASE WHEN sp_atk > 194 THEN 'SUSPICIOUS SP.ATK' ELSE 'OK' END as spatk_check,
                   CASE WHEN sp_def > 230 THEN 'SUSPICIOUS SP.DEF' ELSE 'OK' END as spdef_check
            FROM pokemon
            WHERE hp > 255 OR attack > 190 OR defense > 230 OR sp_atk > 194 OR sp_def > 230 OR pokedex_id > 800
            ORDER BY total DESC
        """, conn)
        conn.close()

        if audit.empty:
            st.success("✅ No cheats detected! Database looks clean.")
        else:
            st.warning(f"⚠️ Found {len(audit)} suspicious Pokemon!")
            st.dataframe(audit, use_container_width=True)

    # Reset database button
    if st.button("🔄 Reset Database (Remove All Cheats)"):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            init_db()
            st.session_state['cheats_applied'] = []
            st.success("✅ Database reset to original state!")
            st.rerun()

# ============================================================
# Task 3.4: Pokemon Insights
# ============================================================
elif tab == "📊 Pokemon Insights":
    st.header("📊 Pokemon Insights")

    conn = get_conn()

    # Insight 1: Most overpowered type combination
    st.subheader("1. Most Overpowered Type Combinations")
    query1 = """
        SELECT type1, type2, COUNT(*) as count,
               ROUND(AVG(total), 1) as avg_total,
               ROUND(AVG(attack), 1) as avg_atk,
               ROUND(AVG(defense), 1) as avg_def,
               ROUND(AVG(speed), 1) as avg_spd
        FROM pokemon
        WHERE type2 IS NOT NULL
        GROUP BY type1, type2
        HAVING count >= 3
        ORDER BY avg_total DESC
        LIMIT 15
    """
    df1 = pd.read_sql_query(query1, conn)
    df1['type_combo'] = df1['type1'] + ' / ' + df1['type2']
    fig1 = px.bar(df1, x='type_combo', y='avg_total',
                  title="Strongest Type Combinations (Avg Total Stats, min 3 Pokemon)",
                  color='avg_total', color_continuous_scale='inferno',
                  hover_data=['avg_atk', 'avg_def', 'avg_spd', 'count'])
    fig1.update_layout(template="plotly_dark", xaxis_tickangle=-45)
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown("""
    **Finding:** Dragon-type combinations consistently rank among the most powerful in the game. 
    Dual-type Pokemon with Dragon typing tend to have the highest average total stats, which makes sense 
    since many Dragon types are pseudo-legendary or legendary Pokemon. The game designers clearly intended 
    Dragon types to be rare and powerful, creating a natural hierarchy within the type system. This is balanced 
    by Dragons being weak to Ice, Fairy, and other Dragon types, so raw stats alone do not guarantee victory.
    """)

    # Insight 2: Power creep across generations
    st.subheader("2. Power Creep Across Generations")
    query2 = """
        SELECT generation,
               COUNT(*) as num_pokemon,
               ROUND(AVG(total), 1) as avg_total,
               ROUND(AVG(hp), 1) as avg_hp,
               ROUND(AVG(attack), 1) as avg_atk,
               SUM(CASE WHEN legendary = 1 THEN 1 ELSE 0 END) as legendaries
        FROM pokemon
        GROUP BY generation
        ORDER BY generation
    """
    df2 = pd.read_sql_query(query2, conn)
    fig2 = px.line(df2, x='generation', y='avg_total',
                   title="Average Total Stats by Generation (Power Creep?)",
                   labels={'generation': 'Generation', 'avg_total': 'Avg Total Stats'},
                   markers=True, color_discrete_sequence=['#FF4444'])
    fig2.update_layout(template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)

    fig2b = px.bar(df2, x='generation', y=['avg_hp', 'avg_atk'],
                   title="HP vs Attack Trends Across Generations",
                   barmode='group', color_discrete_sequence=['#4ECDC4', '#FF6B6B'])
    fig2b.update_layout(template="plotly_dark")
    st.plotly_chart(fig2b, use_container_width=True)
    st.markdown("""
    **Finding:** Looking at the average stats across generations, there is some evidence of power creep but 
    it is not as straightforward as you might expect. Each generation introduces both weak early-route Pokemon 
    and powerful legendaries, which balances the average out. However, later generations tend to have slightly 
    higher average stats overall. The number of legendary Pokemon also varies by generation, and since 
    legendaries have much higher stats, generations with more legendaries will naturally show higher averages. 
    This suggests that power creep in Pokemon is more about introducing stronger outliers rather than raising 
    the baseline for all Pokemon.
    """)

    # Insight 3: Weakest Legendary
    st.subheader("3. The Weakest Legendary Pokemon")
    query3 = """
        SELECT name, type1, type2, total, hp, attack, defense, sp_atk, sp_def, speed, generation
        FROM pokemon
        WHERE legendary = 1
        ORDER BY total ASC
        LIMIT 10
    """
    df3 = pd.read_sql_query(query3, conn)
    fig3 = px.bar(df3, x='name', y='total',
                  title="Weakest Legendary Pokemon by Total Stats",
                  color='total', color_continuous_scale='blues',
                  hover_data=['type1', 'type2', 'generation'])
    fig3.update_layout(template="plotly_dark")
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown("""
    **Finding:** Not all legendaries are created equal. Some legendary Pokemon have surprisingly low stats 
    compared to their peers. These "weaker" legendaries often have unique abilities or roles that compensate 
    for their lower stats, such as support abilities or unique type combinations. This design choice shows 
    that the game designers wanted legendaries to feel special not just through raw power but also through 
    unique characteristics. It also means that simply having a legendary on your team does not guarantee 
    you will win — strategy and type matchups matter more than just picking the rarest Pokemon.
    """)

    conn.close()
