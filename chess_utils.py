import re
import chess
from typing import List, Optional, TypedDict
from collections import defaultdict
from typing import Dict
from dotenv import load_dotenv
import os

load_dotenv()

class PositionSummary(TypedDict):
    fen: str
    white_pieces: List[str]
    black_pieces: List[str]
    legal_moves: List[str]

def summarize_position(fen: str, san = True) -> PositionSummary:
    board = chess.Board(fen)

    white_groups = defaultdict(list)
    black_groups = defaultdict(list)

    for square, piece in board.piece_map().items():
        square_name = chess.square_name(square)
        if piece.color == chess.WHITE:
            white_groups[piece.piece_type].append(square_name)
        else:
            black_groups[piece.piece_type].append(square_name)

    def format_group(groups: Dict[int, list]) -> str:
        names = {
            chess.KING: "king",
            chess.QUEEN: "queen",
            chess.ROOK: "rook",
            chess.BISHOP: "bishop",
            chess.KNIGHT: "knight",
            chess.PAWN: "pawn",
        }
        return "\n ".join(
            f"- {names[ptype]}: {', '.join(sorted(squares))}"
            for ptype, squares in sorted(groups.items())
        )
    legal_moves: List[str] = [board.san(move) for move in board.legal_moves]

    return {
        "fen": fen,
        "white_pieces": format_group(white_groups),
        "black_pieces": format_group(black_groups),
        "legal_moves": legal_moves if san else [str(move) for move in board.legal_moves],
    }

# print(summarize_position(chess.STARTING_FEN, san=False))

def create_prompt(fen: str, san = True) -> str:
    position_summary = summarize_position(fen, san)
    side = "white" if chess.Board(fen).turn == chess.WHITE else "black"

    return f"""
You are tasked with playing the {side} pieces in the following chess position.

The pieces on the board are arranged as follows:
white pieces: {position_summary['white_pieces']}
black pieces: {position_summary['black_pieces']}

Your turn ({side} to move)

Legal moves: {position_summary['legal_moves']}

Your Objective: Select the single best move from the provided list.
Analysis Process:
1. Identify Candidate Moves: Briefly scan the list for active moves: checks, moves threatening mate, moves placing pieces on key squares. Also note moves that place your piece where it can be immediately captured.
2. Mandatory Tactical Calculation (Highest Priority):
 - For every candidate move identified in Step 1, especially checks or moves placing a piece en prise (where it can be captured):
 - Calculate the opponent's primary responses. What are the forced replies? What happens if the opponent captures the piece you just moved?
 - Evaluate the position after the opponent's likely reply.
 - If your move places a piece en prise: Does the opponent capturing it lead to your checkmate shortly after? Does it lead to you winning more material than you lost? Does it gain a decisive, unavoidable advantage? If yes, this is a potential sacrifice.
 - If your move places a piece en prise and the opponent capturing it simply results in you losing material with no significant compensation, this is a blunder. Eliminate this move from consideration.
 - If your move is a check: Are all opponent responses safe for you? Does any response capture your checking piece? If yes, evaluate the consequences as described above (is it a sacrifice leading to mate, or a blunder?).
3. Eliminate Blunders: Discard any move confirmed as a blunder in Step 2 (uncompensated loss of material or leading to a worse position).
4. Compare Sound Candidates:
 - Evaluate the remaining moves (safe moves and sound sacrifices).
 - Prioritize forcing lines that lead to checkmate quickly (like a sound sacrifice leading to mate, or a check sequence leading to mate).
 - If no immediate mate is found, choose the move that provides the greatest advantage safely.
5. Final Selection:
 - Choose exactly one move from the legal moves list that survived the tactical calculation and comparison.
"""

import requests

def send_prompt(prompt: str, model: str, server_url: str = "https://openrouter.ai/api/v1/chat/completions") -> Optional[str]:
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }

    response = requests.post(server_url,
                             headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
                             json=payload)

    if response.status_code == 200:
        content = response.json()["choices"][0]["message"]["content"]
        return content.strip()
    else:
        print(f"Request failed with status code {response.status_code}")
        print(response.text)
        return None

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
