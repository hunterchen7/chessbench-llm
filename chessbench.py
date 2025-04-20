import chess_utils
import chess

def create_prompt(fen: str) -> str:
    position_summary = chess_utils.summarize_position(fen)

    return f"""
You are a world-class chess grandmaster and you are playing a chess game.

These are the pieces on the board:

white pieces: {position_summary['white_pieces']}

black pieces: {position_summary['black_pieces']}

These are the legal moves you may make:

legal moves: {position_summary['legal_moves']}

Select exactly one move from the list of legal moves given.
"""

import requests

def send_prompt(prompt: str, server_url: str = "http://127.0.0.1:8000/v1/chat/completions"):
    payload = {
        "model": "qwen",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.9
    }

    response = requests.post(server_url, json=payload)

    if response.status_code == 200:
        content = response.json()["choices"][0]["message"]["content"]
        # print("Model response:")
        # print(content.strip())
        return content.strip()
    else:
        print(f"Request failed with status code {response.status_code}")
        print(response.text)
        return None

import chess
from typing import Optional

def parse_response(fen: str, response: str) -> Optional[str]:
    board = chess.Board(fen)
    legal_moves = list(board.legal_moves)

    earliest = None
    earliest_pos = float("inf")

    for move in legal_moves:
        san = board.san(move)
        idx = response.find(san)
        if idx != -1 and idx < earliest_pos:
            earliest = move
            earliest_pos = idx

    return earliest  # returns a `chess.Move` object

if __name__ == "__main__":
    position = chess.STARTING_FEN
    board = chess.Board(position)
    move_history = []

    while not board.is_game_over():
        print("\n=== Turn", board.fullmove_number, ("White" if board.turn else "Black"), "===")
        prompt = create_prompt(board.fen())
        response = send_prompt(prompt)
        move = parse_response(board.fen(), response)

        if move is None:
            print("Failed to extract a legal move. Game aborted.")
            print("Model response:", response)
            break

        try:
            if move not in board.legal_moves:
                print(f"Illegal move from model: {board.san(move)}. Game aborted.")
                break
            san = board.san(move)
            board.push(move)
            move_history.append(san)
            print(f"Move played: {san}")
            print(board)
        except Exception as e:
            print(f"Error parsing move: {e}")
            break

    print("\n=== Game Over ===")
    print("Result:", board.result())
    print("Final FEN:", board.fen())
    print("\nMoves played:")
    for i, san in enumerate(move_history, start=1):
        turn = "White" if i % 2 != 0 else "Black"
        print(f"{i:02d}. {turn}: {san}")