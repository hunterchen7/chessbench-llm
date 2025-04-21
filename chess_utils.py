import chess
from typing import List, TypedDict
from collections import defaultdict
from typing import Dict

class PositionSummary(TypedDict):
    fen: str
    white_pieces: List[str]
    black_pieces: List[str]
    legal_moves: List[str]

def summarize_position(fen: str) -> PositionSummary:
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
        "legal_moves": legal_moves,
    }

print(summarize_position(chess.STARTING_FEN))