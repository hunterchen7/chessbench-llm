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

def create_puzzle_prompt(fen: str, san = True) -> str:
    position_summary = summarize_position(fen, san)
    side = "white" if chess.Board(fen).turn == chess.WHITE else "black"

    return f"""
You are playing a chess puzzle as {side}. Find the best move in this position: {position_summary}
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
