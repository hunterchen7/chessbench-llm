import pandas as pd
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from puzzles_utils import parse_puzzle

# Load CSV once into memory
df = pd.read_csv("lichess_puzzles_1000_plays.csv")
df = df[df["Rating"].notna()]  # Clean any rows with missing ratings
df["Rating"] = df["Rating"].astype(int)

app = FastAPI()

@app.get("/random-puzzle")
def get_random_puzzle(min_rating: int = Query(0), max_rating: int = Query(3000)):
    filtered = df[(df["Rating"] >= min_rating) & (df["Rating"] <= max_rating)]
    if filtered.empty:
        return JSONResponse({"error": "No puzzle found in rating range"}, status_code=404)
    row = filtered.sample(n=1).iloc[0]
    return parse_puzzle(row)

"""
import pandas as pd

# Load only the necessary columns
cols = ["PuzzleId","FEN", "Moves", "Rating", "NbPlays"]
df = pd.read_csv("lichess_puzzles_mega.csv", usecols=cols)

# Drop rows with missing ratings
df = df.dropna(subset=["Rating", "NbPlays"])
df = df[df["NbPlays"] >= 1000]
df["Rating"] = df["Rating"].astype(int)

df = df[["PuzzleId", "FEN", "Moves", "Rating"]]

# Save to new CSV
df.to_csv("lichess_puzzles_1000_plays.csv", index=False)


import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv
load_dotenv()



# postgresql://chessbench_owner:npg_oNk9APW8uLbf@ep-curly-frost-a4aab9iv-pooler.us-east-1.aws.neon.tech/chessbench?sslmode=require

# Database connection info
conn = psycopg2.connect(
    dbname="chessbench",
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
)
cur = conn.cursor()

# Create table if it doesn't exist
cur.execute("""
"""CREATE TABLE IF NOT EXISTS puzzles (
    id TEXT PRIMARY KEY,
    fen TEXT NOT NULL,
    moves TEXT NOT NULL,
    rating INTEGER NOT NULL
)"""
""")

# Load the trimmed CSV
df = pd.read_csv("lichess_puzzles_trimmed.csv")

# Prepare data
records = list(df.itertuples(index=False, name=None))

# Bulk insert
execute_values(
    cur,
    "INSERT INTO puzzles (id, fen, moves, rating) VALUES %s ON CONFLICT (id) DO NOTHING",
    records
)


conn.commit()
cur.close()
conn.close()
"""
