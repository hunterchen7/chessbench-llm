import csv
import chess
import json

def parse_puzzle(row):
    fen = row["FEN"]
    moves = row["Moves"].split()
    board = chess.Board(fen)
    rating = int(row["Rating"])
    puzzle_turn = board.turn  # side to play in the puzzle
    steps = []

    for i, expected_uci in enumerate(moves):
        if board.turn != puzzle_turn:
            # record only this side's turn
            move_obj = chess.Move.from_uci(expected_uci)
            try:
                san = board.san(move_obj)
            except Exception:
                san = None  # fallback, rare in clean puzzles

            steps.append({
                "fen": board.fen(),
                "expected_uci": expected_uci,
                "expected_san": san,
            })

        # apply the move regardless of who played it
        try:
            board.push_uci(expected_uci)
        except Exception as e:
            print(f"Invalid move {expected_uci} in puzzle {row['PuzzleId']}: {e}")
            break

    return {
        "puzzle_id": row["PuzzleId"],
        "steps": steps,
        "rating": rating,
    }

def parse_puzzles_from_csv(csv_file):
    all_puzzles = []

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["FEN"] and row["Moves"] and row["Rating"]:
                try:
                    puzzle = parse_puzzle(row)
                    all_puzzles.append(puzzle)
                except Exception as e:
                    print(f"Error parsing puzzle {row['PuzzleId']}: {e}")

    all_puzzles.sort(key=lambda x: x["rating"])

    return all_puzzles

puzzles = parse_puzzles_from_csv("lichess_puzzles_small.csv")

with open("puzzles_small.json", "w", encoding="utf-8") as f:
    json.dump(puzzles, f, indent=2)


import csv
import multiprocessing
from collections import Counter
import matplotlib.pyplot as plt
from tqdm import tqdm

CSV_PATH = "lichess_puzzles_mega.csv"
# CSV_PATH = "lichess_puzzles_small.csv"
NUM_WORKERS = multiprocessing.cpu_count()
CHUNK_SIZE = 100_000

def process_chunk(lines):
    rating_counter = Counter()
    for line in lines:
        try:
            rating = int(line["RatingDeviation"])
            rating_bucket = rating  # group by 3s
            rating_counter[rating_bucket] += 1
        except (ValueError, KeyError):
            continue
    return rating_counter

def chunkify_csv(path, chunk_size=CHUNK_SIZE):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        chunk = []
        for row in reader:
            chunk.append(row)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

if __name__ == "__main__":
    with multiprocessing.Pool(NUM_WORKERS) as pool:
        results = list(tqdm(pool.imap(process_chunk, chunkify_csv(CSV_PATH)), desc="Processing"))

    # Combine counters
    total_counts = Counter()
    for partial in results:
        total_counts.update(partial)

    # Sort and prepare
    sorted_ratings = sorted(total_counts.items())
    x = [r for r, _ in sorted_ratings]
    y = [c for _, c in sorted_ratings]

    # Plot
    plt.figure(figsize=(14, 6))
    plt.bar(x, y, width=4)
    plt.title("Distribution of Lichess Rating Deviations")
    plt.xlabel("Rating")
    plt.ylabel("Number of Puzzles")
    plt.grid(axis="y")

    # More readable x-axis ticks
    plt.xticks(x[::1 if len(x) < 30 else 2], rotation=45)  # dynamic spacing
    plt.tight_layout()
    plt.show()
