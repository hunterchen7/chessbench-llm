import csv, os
from psycopg2 import connect, extras
from dotenv import load_dotenv
load_dotenv()

BATCH = 1

conn = connect(
    dbname="matches",
    user=os.getenv("MATCHES_DB_USER"),
    password=os.getenv("MATCHES_DB_PASSWORD"),
    host=os.getenv("MATCHES_DB_HOST"),
)
conn.autocommit = False
data = []

with open("lkichess_puzzles_zzzz.csv", newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):

        if (row["FEN"] and row["Moves"] and row["Rating"] and
            row["GameUrl"] and row["NbPlays"] and int(row["NbPlays"]) >= 1000 and row["PuzzleId"]):
            slug = row["GameUrl"].split("lichess.org/")[-1]
            data.append((row["PuzzleId"], slug))

        if len(data) >= BATCH:
            with conn.cursor() as cur:
                extras.execute_values(
                    cur,
                    """
                    UPDATE puzzles AS p
                    SET    url_slug = v.url
                    FROM   (VALUES %s) AS v(id, url)
                    WHERE  p.id = v.id
                    """,
                    data,
                    page_size=BATCH
                )
            data.clear()

# flush final partial batch
if data:
    with conn.cursor() as cur:
        extras.execute_values(
            cur,
            """
            UPDATE puzzles AS p
            SET    url_slug = v.url
            FROM   (VALUES %s) AS v(url, id)
            WHERE  p.id = v.id
            """,
            data
        )

conn.commit()
conn.close()
