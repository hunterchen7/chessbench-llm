import itertools
import chess_utils
import chess
from typing import List, Optional, Tuple
import time
import json
from dotenv import load_dotenv
import os

load_dotenv()

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
        # print("Model response:")
        # print(content.strip())
        return content.strip()
    else:
        print(f"Request failed with status code {response.status_code}")
        print(response.text)
        return None

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

models = [
    "meta-llama/llama-4-maverick:free",
    "qwen/qwq-32b:free",
]

def generate_matches(models: List[str]) -> List[Tuple[str, str]]:
    return list(itertools.permutations(models, 2))

if __name__ == "__main__":
    matches = generate_matches(models)

    for white_model, black_model in matches:
        print(f"\n=== Starting game: {white_model} vs {black_model} ===")
        timestamp = time.strftime("%Y%m%d-%H%M%S")

        position = chess.STARTING_FEN
        board = chess.Board(position)
        move_history = []
        game_trace = []

        while not board.is_game_over():
            print("\n=== Turn", board.fullmove_number, ("White" if board.turn else "Black"), "===")
            prompt = create_prompt(board.fen())
            response = send_prompt(prompt, white_model if board.turn == chess.WHITE else black_model)
            move = parse_response(board.fen(), response)

            if move is None:
                print("Failed to extract a legal move. Game aborted.")
                print("Model response:", response)
                break

            try:
                if move not in board.legal_moves:
                    print(f"Illegal move from model: {board.san(move)}. Game aborted.")
                    print("Model response:", response)
                    break
                san = board.san(move)
                game_trace.append({
                    "turn": board.fullmove_number,
                    "side": "White" if board.turn == chess.WHITE else "Black",
                    "fen_before": board.fen(),
                    "move": san,
                    "response": response.strip(),
                })
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
        for i in range(0, len(move_history), 2):
            move_num = i // 2 + 1
            white_move = move_history[i]
            black_move = move_history[i + 1] if i + 1 < len(move_history) else "—"
            print(f"{move_num}. {white_move} {black_move}")

        game_data = {
            "result": board.result(),
            "final_fen": board.fen(),
            "moves": game_trace,
        }
        filename = f"game_{timestamp}_{white_model}_{black_model}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(game_data, f, indent=2)
        print(f"\nGame data saved to {filename}")
