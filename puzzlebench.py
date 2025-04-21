import os
import time
import psycopg2
from chess_utils import create_prompt, extract_move, send_prompt, rating_change, compute_outcome
from puzzles_small import select_puzzles
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(
    dbname="matches",
    user=os.getenv("MATCHES_DB_USER"),
    password=os.getenv("MATCHES_DB_PASSWORD"),
    host=os.getenv("MATCHES_DB_HOST"),
)

test_puzzles = select_puzzles

models = [
    'qwen/qwq-32b',
    'deepseek/deepseek-chat-v3-0324',
    'deepseek/deepseek-r1',
    'google/gemini-2.0-flash-lite-001',
    'google/gemini-2.5-flash-preview',
    'google/gemini-2.5-pro-preview-03-25',
    'openai/gpt-4.1-nano',
    'openai/o3-mini-high',
    'openai/o4-mini-high',
]

# insert models into database with 1500 rating if not exists

with conn.cursor() as cur:
    for model in models:
        cur.execute("""
            INSERT INTO players (name, rating)
            VALUES (%s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (model, 1500))

    conn.commit()
    print("Models inserted into database.")

for puzzle in test_puzzles:
    puzzle_id = puzzle['puzzle_id']
    steps = puzzle['steps']
    rating = puzzle['rating']

    for model in models:
        curr_time = time.strftime("%Y%m%d-%H%M%S")
        print(f"Testing {model} on puzzle {puzzle_id} with rating {rating}")

        # get the model's rating from the database
        with conn.cursor() as cur:
            cur.execute("""
                SELECT rating FROM players WHERE name = %s
            """, (model,))
            result = cur.fetchone()
            if result:
                model_rating = result[0]
            else:
                print(f"Model {model} not found in database.")
                continue

            # check if the model has played this puzzle before
            cur.execute("""
                SELECT COUNT(*) FROM matches WHERE player = %s AND puzzle = %s
            """, (model, puzzle_id))
            count = cur.fetchone()[0]
            if count > 0:
                print(f"Model {model} has already played puzzle {puzzle_id}. Skipping.")
                continue

        moves_played = []
        for step in steps:
            fen = step['fen']
            expected_uci = step['expected_uci']
            expected_san = step['expected_san']

            print(f"Expected UCI: {expected_uci}, Expected SAN: {expected_san}")

            prompt = create_prompt(fen)
            res = send_prompt(prompt, model)

            extracted_move = extract_move(res, fen)
            print(f"Extracted move: {extracted_move}")
            moves_played.append(extracted_move)

            if extracted_move != expected_san:
                print(f"Test failed for {model} on puzzle {puzzle_id} at step {fen}")
                print(f"Expected: {expected_san}, Got: {extracted_move}")
                break

        rating_change_value = rating_change(model_rating, rating, compute_outcome(moves_played, steps))
        print(f"Rating change for {model} on puzzle {puzzle_id}: {rating_change_value}")

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO matches (player, puzzle, moves_played, rating_change, time)
                VALUES (%s, %s, %s, %s, NOW())
            """, (
                model,                  # player name
                puzzle_id,              # puzzle ID
                ",".join(moves_played), # moves played as CSV string
                rating_change_value     # numeric(5,1)
            ))
            cur.execute("""
                UPDATE players
                SET rating = %s
                WHERE name = %s
            """, (model_rating + rating_change_value, model))
            conn.commit()
