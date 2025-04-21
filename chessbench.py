import itertools
import re
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
    side = "white" if chess.Board(fen).turn == chess.WHITE else "black"

    return f"""
You are a world-class chess grandmaster playing as {side}.

The pieces on the board are arranged as follows:
white pieces: {position_summary['white_pieces']}
black pieces: {position_summary['black_pieces']}

These are the legal moves you may make: {position_summary['legal_moves']}

You are to select the best move from the list of legal moves given.

Crucially, evaluate the position and consider the potential consequences of the move you are about to make.

Look carefully for any potential checks, captures, or threats your opponent could make in response to your move.

Also look carefully for tactics such as forks, pins, and skewers that could be used against you.

To reiterate, your goal is to a find the strongest move that is legal, and to avoid blundering at all cost.

Select exactly one move from the list of legal moves given, you may choose to briefly justify your choice.
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
        print("Model response:")
        print(content.strip())
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
            "model": "meta-llama/llama-4-scout:free",
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

models = [
    "meta-llama/llama-4-maverick:free",
    "google/gemini-2.5-flash-preview",
]

def sanitize_filename(s: str) -> str:
    return s.replace("/", "_").replace(":", "-")

def generate_matches(models: List[str]) -> List[Tuple[str, str]]:
    return list(itertools.permutations(models, 2))

if __name__ == "__main__":
    matches = generate_matches(models)

    for white_model, black_model in matches:
        print(f"\n=== Starting game: {white_model} vs {black_model} ===")
        timestamp = time.strftime("%Y%m%d-%H%M%S")

        safe_white = sanitize_filename(white_model)
        safe_black = sanitize_filename(black_model)
        filename = f"game_{timestamp}_{safe_white}_{safe_black}.json"

        position = chess.STARTING_FEN
        board = chess.Board(position)
        move_history = []
        game_trace = []

        while not board.is_game_over():
            print("\n=== Turn", board.fullmove_number, ("White" if board.turn else "Black"), "===")
            curr_model = white_model if board.turn == chess.WHITE else black_model
            prompt = create_prompt(board.fen())
            print('prompting ', curr_model)
            response = send_prompt(prompt, curr_model)
            print('extracting move from response..')
            san_move = parse_move(board.fen(), extract_move_scout(response))
            print('extracted move:', san_move)
            move = board.parse_san(san_move) if san_move else None

            if move is None:
                print("Failed to extract a legal move. Game aborted.")
                print("Model response:", response)
                print("extracted move:", san_move)
                break

            try:
                if move not in board.legal_moves:
                    print(f"Illegal move from model: {move}. Game aborted.")
                    print("Model response:", response)

                    game_trace.append({
                        "turn": board.fullmove_number,
                        "side": "White" if board.turn == chess.WHITE else "Black",
                        "fen_before": board.fen(),
                        "move": "ILLEGAL",
                        "prompt": prompt,
                        "response": response.strip(),
                        "note": "Illegal move"
                    })

                    # Mark win for the opponent
                    board_result = "0-1" if board.turn == chess.WHITE else "1-0"

                    game_data = {
                        "result": board_result,
                        "final_fen": board.fen(),
                        "moves": game_trace,
                    }

                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(game_data, f, indent=2)

                    print(f"Result (due to illegal move): {board_result}")
                    print(f"\nGame data saved to {filename}")
                    break

                game_trace.append({
                    "turn": board.fullmove_number,
                    "side": "White" if board.turn == chess.WHITE else "Black",
                    "fen_before": board.fen(),
                    "move": san_move,
                    "prompt": prompt,
                    "response": response.strip(),
                })

                game_data = {
                    "result": board.result() if board.is_game_over() else None,
                    "final_fen": board.fen(),
                    "moves": game_trace,
                }
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(game_data, f, indent=2)

                board.push(move)
                move_history.append(san_move)
                print(f"Move played: {san_move}")
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

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(game_data, f, indent=2)
        print(f"\nGame data saved to {filename}")
