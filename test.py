import chess
from chess_utils import summarize_position

board = chess.Board('8/r4k2/7R/3n1PK1/8/8/8/8 w - - 4 57')

# moves:

print(summarize_position(board.fen(), san=True))

