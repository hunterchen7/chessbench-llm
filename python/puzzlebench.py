import os
import psycopg2
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from chess_utils import extract_move, rating_change, compute_outcome
from prompt_utils import create_puzzle_prompt, send_prompt
# from puzzles_small import select_puzzles
from puzzle_server import get_random_puzzle
from psycopg2.extras import Json

load_dotenv()

PUZZLES = 47

# Connect to Postgres

# Define models and insert them with default rating
models = [
    # 'qwen/qwq-32b',
    # 'deepseek/deepseek-chat-v3-0324',
    # 'deepseek/deepseek-r1',
    # 'google/gemini-2.0-flash-lite-001',
    # 'google/gemini-2.5-flash-preview',
    # 'google/gemini-2.5-pro-preview-03-25',
    # 'openai/gpt-4.1-nano',
    # 'openai/o3-mini-high',
    # 'openai/o4-mini-high',
    'openai/gpt-4.1',
    # 'meta-llama/llama-4-scout',
    # 'meta-llama/llama-4-maverick',
    'qwen/qwen-max',
    # 'openai/gpt-4.1-mini',
    'x-ai/grok-3-mini-beta',
    'x-ai/grok-3-beta',
    'anthropic/claude-3.7-sonnet',
]

# insert into db if not exists

conn = psycopg2.connect(
        dbname="matches",
        user=os.getenv("MATCHES_DB_USER"),
        password=os.getenv("MATCHES_DB_PASSWORD"),
        host=os.getenv("MATCHES_DB_HOST"),
    )

with conn.cursor() as cur:
    for model in models:
        cur.execute("""
            INSERT INTO players (name, rating) VALUES (%s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (model, 800))
    conn.commit()

conn.close()


# Load test puzzles
# test_puzzles = select_puzzles

def run_model_on_puzzle(model, puzzle, conn):
    puzzle_id = puzzle['puzzle_id']
    steps = puzzle['steps']
    rating = puzzle['rating']
    moves_played = []
    responses = []
    matches_played = 0

    try:
        with conn.cursor() as cur:
            # Get current model rating
            cur.execute("SELECT rating FROM players WHERE name = %s", (model,))
            result = cur.fetchone()
            if not result:
                return f"Model {model} not found."
            model_rating = result[0]

            # Skip if already attempted
            cur.execute("SELECT COUNT(*) FROM matches WHERE player = %s AND puzzle = %s", (model, puzzle_id))
            if cur.fetchone()[0] > 0:
                return f"{model} already played {puzzle_id}, skipping."

            # get number of matches played
            cur.execute("SELECT COUNT(*) FROM matches WHERE player = %s", (model,))
            matches_played = cur.fetchone()[0]

        print(f"Testing {model} on puzzle {puzzle_id} (rating {rating})")

        # Step through puzzle
        for step in steps:
            fen = step['fen']
            expected_san = step['expected_san']

            prompt = create_puzzle_prompt(fen)
            res = send_prompt(prompt, model)
            responses.append(res)
            move = extract_move(res, fen)
            # print(f"{model} move: {move} | expected: {expected_san}")
            moves_played.append(move)

            if move != expected_san:
                break

        print(f"played moves: {moves_played}, expected: {[step['expected_san'] for step in steps]}")

        # Evaluate and update
        outcome = compute_outcome(moves_played, [step['expected_san'] for step in steps])
        delta = round(rating_change(model_rating, rating, outcome, matches_played), 1)

        notes = [
            {
                "ply": idx + 1,        # 1‑based move number
                "move": move,          # SAN string you extracted
                "response": res     # full text returned by the model
            }
            for idx, (move, res) in enumerate(zip(moves_played, responses))
        ]

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO matches (player, puzzle, notes, rating_change, time)
                VALUES (%s, %s, %s, %s, NOW())
            """, (model, puzzle_id, Json(notes), delta))
            cur.execute("""
                UPDATE players SET rating = %s WHERE name = %s
            """, (round(model_rating + delta, 1), model))
            conn.commit()

        return f"{model} finished puzzle {puzzle_id} (Δ={delta})"
    except Exception as e:
        return f"Error for {model} on {puzzle_id}: {e}"

def run_model_thread(model, N: int = PUZZLES, RATING_TOLERANCE: int = 50):
    print(f"Starting thread for {model}...")
    conn = psycopg2.connect(
        dbname="matches",
        user=os.getenv("MATCHES_DB_USER"),
        password=os.getenv("MATCHES_DB_PASSWORD"),
        host=os.getenv("MATCHES_DB_HOST"),
    )

    with conn.cursor() as cur:
        # Get puzzles already seen
        cur.execute("SELECT puzzle FROM matches WHERE player = %s", (model,))
        seen = {row[0] for row in cur.fetchall()}

    puzzles_done = 0
    while puzzles_done < N:
        # Refresh rating to keep matchmaking aligned with progress
        with conn.cursor() as cur:
            cur.execute("SELECT rating FROM players WHERE name = %s", (model,))
            model_rating = cur.fetchone()[0]

        min_rating = model_rating - RATING_TOLERANCE
        max_rating = model_rating + RATING_TOLERANCE

        # Try to get a puzzle within rating range
        candidate = get_random_puzzle(min_rating=min_rating, max_rating=max_rating)

        if not candidate or candidate["puzzle_id"] in seen:
            continue  # try again

        result = run_model_on_puzzle(model, candidate, conn)
        print(result)

        seen.add(candidate["puzzle_id"])
        puzzles_done += 1
        print(f"Completed {puzzles_done}/{N} puzzles for {model}")

    conn.close()

# Run all models on all puzzles in parallel (per puzzle)
"""for puzzle in test_puzzles:
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_model_on_puzzle, model, puzzle) for model in models]
        for future in as_completed(futures):
            print(future.result())
"""

with ThreadPoolExecutor(max_workers=len(models)) as executor:
    executor.map(run_model_thread, models)

