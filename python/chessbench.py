import itertools
from chess_utils import create_prompt, extract_move, send_prompt
import chess
from typing import List, Tuple
import time
import json

models = [
    "openai/gpt-4.1-nano",
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

            san_move = extract_move(response, board.fen())

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
                    "white": white_model,
                    "black": black_model,
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
        moves_played = ""
        for i in range(0, len(move_history), 2):
            move_num = i // 2 + 1
            white_move = move_history[i]
            black_move = move_history[i + 1] if i + 1 < len(move_history) else "—"
            move = f"{move_num}. {white_move} {black_move}"
            moves_played += move
            print(move)

        game_data = {
            "white": white_model,
            "black": black_model,
            "result": board.result(),
            "final_fen": board.fen(),
            "moves": game_trace,
            "san_moves": moves_played
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(game_data, f, indent=2)
        print(f"\nGame data saved to {filename}")
