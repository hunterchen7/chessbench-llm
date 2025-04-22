import re
import chess
from typing import List, Optional, TypedDict
from collections import defaultdict
from typing import Dict
from dotenv import load_dotenv
import os

import requests

load_dotenv()

def parse_move(fen: str, response: str) -> Optional[str]:
    board = chess.Board(fen)
    legal_moves = list(board.legal_moves)

    for move in legal_moves:
        san = board.san(move)
        if san in response:
            return san

def extract_move_scout(response_text: str) -> str:
    prompt = f"""You are an assistant that extracts the final chess move selected from a grandmaster-style explanation.

The move must be in SAN (Standard Algebraic Notation), such as: e4, d4, Nf3, Nc6, O-O, Qxe5, etc.

Only return the move that the player finally decided to play. Ignore other candidate moves that were discussed but rejected. If multiple moves are mentioned, return the one that is clearly stated as the final or best choice.

Respond with **only** the SAN move, and nothing else.

Text:
\"\"\"
{response_text}
\"\"\"

Final Move:"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "meta-llama/llama-4-scout",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        raise RuntimeError(f"Extraction failed: {response.status_code}\n{response.text}")

def extract_san_heuristically(response: str, fen: str) -> str:
    board = chess.Board(fen)
    legal_sans = [board.san(move) for move in board.legal_moves]

    # Regex for all SAN-like tokens
    candidates = re.findall(r'\b([KNBRQ]?[a-h]?[1-8]?x?[a-h][1-8]|O-O(?:-O)?)\b', response)

    # Score based on position in text
    for move in candidates:
        if move in legal_sans:
            # Try to find a confirming phrase near it
            before = response[:response.find(move)].lower()
            if any(kw in before[-100:] for kw in ["final answer", "i choose", "best move", "i played", "my move", "i play", "i will play", "i select", "my chosen"]):
                return move

    # Fallback: return first legal SAN found
    for move in candidates:
        if move in legal_sans:
            return move

    return None

def extract_move(response: str, fen: str) -> Optional[str]:
    # First try the scout model
    try:
        return parse_move(fen, extract_move_scout(response))
    except Exception as e:
        print(f"Scout extraction failed: {e}")

    # If scout fails, use heuristic extraction
    return extract_san_heuristically(response, fen)

# elo
def compute_outcome(player_moves, correct_moves_list):
    correct_moves = 0
    for p, c in zip(player_moves, correct_moves_list):
        if p != c:
            break
        correct_moves += 1

    total_moves = len(correct_moves_list)
    if correct_moves == total_moves:
        return 1.0
    elif correct_moves >= total_moves // 2:
        return 0.5
    else:
        return 0.0

def expected_score(player_rating: int, puzzle_rating: int) -> float:
    return 1 / (1 + 10 ** ((puzzle_rating - player_rating) / 400))

def get_k(num_matches_played, start_k=256, min_k=16, decay_cap=12):
    if num_matches_played >= decay_cap:
        return min_k
    # Linearly decay from start_k to min_k over `decay_cap` games
    decay_rate = (start_k - min_k) / decay_cap
    return round(start_k - decay_rate * num_matches_played)

def rating_change(player_rating: int, puzzle_rating: int, outcome: float, matches_played: int) -> float:
    K = get_k(matches_played)
    expected = expected_score(player_rating, puzzle_rating)
    return K * (outcome - expected)
