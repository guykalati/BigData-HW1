# 📊 HW1 - Big Data & SQL

Interactive SQL applications built with Python, SQLite, SQLAlchemy, and Streamlit.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run any task
streamlit run task1_baby_names/app.py    # Baby Names Explorer
streamlit run task2_oscar/app.py         # Oscar Actor Explorer
streamlit run task3_pokemon/app.py       # Pokemon Battle Arena
streamlit run task4_sql_learning/app.py  # SQL Learning Game
```

## 📁 Project Structure

```
HW1/
├── data/                    # Datasets (CSV files)
│   ├── NationalNames.csv    # US Baby Names
│   ├── the_oscar_award.csv  # Oscar nominations
│   └── Pokemon.csv          # Pokemon stats
├── task1_baby_names/
│   └── app.py              # Baby Names Explorer (SQLite + Streamlit)
├── task2_oscar/
│   └── app.py              # Oscar Actor Explorer (SQLAlchemy ORM + Wikipedia API)
├── task3_pokemon/
│   └── app.py              # Pokemon Battle Arena (SQLite + Streamlit)
├── task4_sql_learning/
│   └── app.py              # Detective SQL Learning Game
├── REPORT.md               # Detailed report for each task
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## 📋 Tasks Overview

### Task 1: Baby Names Explorer 👶
Explore US baby name trends from 1880 to 2014 using SQLite.
- **Name Popularity Over Time**: Line charts with raw count and percentage modes
- **Custom SQL Query Panel**: Write and execute SELECT queries with built-in examples
- **Name Diversity Analysis**: Unique names per year, gender breakdown, gender-neutral names
- **Pattern Discovery**: 3 data-driven insights with visualizations

### Task 2: Oscar Actor Explorer 🏆
Browse Oscar nominees and winners using SQLAlchemy ORM (no raw SQL).
- **Actor Profile Cards**: Nominations, wins, win rate, categories, films
- **Wikipedia Integration**: Live bio summaries and photos via REST API
- **Interesting Finds**: Most nominations without wins, longest wait to win, competitive categories
- **Did You Know?**: Fun fact generator for any nominee

### Task 3: Pokémon Battle Arena ⚔️
Simulate Pokemon battles with stats from an SQLite database.
- **Battle System**: Speed-based turn order, type effectiveness from DB, battle log
- **Cheat Codes**: 5 cheats that modify the DB (UPUPDOWNDOWN, GODMODE, MAXPOWER, LEGENDARY, NERF)
- **Cheat Audit**: Query to detect modified Pokemon stats
- **Insights**: Analysis of type combinations, power creep, and legendary stats

### Task 4: Detective SQL 🕵️
A story-driven SQL learning game with 7 progressive levels.
- **Theme**: Solve crimes by querying a suspects/evidence database
- **7 Levels**: SELECT → WHERE → ORDER BY/LIMIT → GROUP BY → JOIN → Complex queries → Subqueries
- **Gamification**: Points, streaks, achievements, and progress tracking
- **Feedback System**: Helpful hints, not just "incorrect"

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3, SQLite3 |
| ORM | SQLAlchemy (Task 2) |
| Web Framework | Streamlit |
| Visualizations | Plotly |
| External API | Wikipedia REST API |

## 📝 Datasets

- [US Baby Names](https://www.kaggle.com/kaggle/us-baby-names) — 1.8M name records (1880-2014)
- [The Oscar Award](https://www.kaggle.com/datasets/unanimad/the-oscar-award) — 11K+ nominations
- [Pokemon Dataset](https://www.kaggle.com/datasets/abcsds/pokemon) — 800 Pokemon with stats
