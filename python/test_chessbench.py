from chessbench import extract_san_heuristically

res1 = """As a grandmaster, the best move from the given options is e4.

Reasoning:

Controlling the Center: The move e4 immediately takes control of the center of the board and opens lines for the king’s bishop and queen. Central pawn moves (e4 and d4) are generally the strongest starting moves in chess.


Developing the Bishop: By playing e4, the kingside bishop is freed to develop on a strong diagonal (e.g., bishop on f4 or g5 later).


King’s Knight Development: This move complements Nf3, which is typically played next to develop the knight, attack the e-pawn, and prepare to castle kingside.


Flexibility: Unlike d3 or e3, e4 keeps the d4 square open for the dark-squared bishop or future pawn play.


Other Strong Alternatives:

Nf3 – A solid move, but it doesn't challenge Black’s control of the center.

e4 – The most aggressive and strategically sound choice.

d4 – A viable alternative, but playing e4 first is preferred.

Best Move: e4.
This move pressures Black from the start and allows for quick development and king safety later. Now, Black will likely respond with e5 to challenge the pawn, leading to an Open Game (1.e4 e5). Alternatively, they can play d5 (1.e4 d5) to reach the Scandinavian Defense, but e5 is more common.

Would you like to see the next moves based on Black’s response?"""

res2 = """
Step 1: Understand the given position
The given position is the starting position of a chess game. All pieces are in their initial positions.

Step 2: Recall common opening principles
In the opening, it's generally advantageous to control the center of the board, develop pieces, and ensure the safety of the king. Moving pawns in front of the king and developing knights and bishops are common initial strategies.

Step 3: Analyze the given legal moves
The provided legal moves are: ['Nh3', 'Nf3', 'Nc3', 'Na3', 'h3', 'g3', 'f3', 'e3', 'd3', 'c3', 'b3', 'a3', 'h4', 'g4', 'f4', 'e4', 'd4', 'c4', 'b4', 'a4']. These moves involve developing knights and moving pawns.

Step 4: Evaluate the moves based on opening principles

Moving a knight to a good square is a good start. 'Nf3' is a popular choice as it develops a knight, prepares to develop other pieces, and controls the center indirectly.

'Nc3' also develops a knight and supports the center.

Moving pawns to 'e4' or 'd4' is a common central pawn push, which directly controls the center and opens lines for other pieces.

Step 5: Identify the best move among the given options
Among the given moves, 'Nf3' is a strong candidate because it develops a knight to a good square, doesn't weaken the kingside significantly, and is a flexible move that doesn't commit to a specific pawn structure too early. 'Nc3' is also a good move for similar reasons. 'e4' is a very aggressive and common move that directly challenges the center.

Step 6: Choose between 'Nf3', 'Nc3', and other pawn moves

'Nf3' and 'Nc3' are both good developmental moves.

'e4' is a strong central pawn move that is not listed among the legal moves given.

Step 7: Select the best available move
Since 'e4' is not an option, we look at the next best alternatives. 'Nf3' and 'Nc3' are both excellent. 'Nf3' is often considered one of the most versatile and safe opening moves as it doesn't commit to a specific setup too early and prepares for further development.

Step 8: Final decision
Between 'Nf3' and 'Nc3', both are good. However, 'Nf3' is slightly more popular and considered a very solid choice because it doesn't directly interfere with the potential development of the dark-squared bishop and other pieces.

The final answer is: $\boxed{Nf3}$"""

"""extraction1 = extract_move(res1)

print(f"Extracted move from response 1: {extraction1}")

extraction2 = extract_move(res2)

print(f"Extracted move from response 2: {extraction2}")"""

import chess

heuristic_extraction1 = extract_san_heuristically(res1, chess.STARTING_FEN)
print(f"Heuristic extraction from response 1: {heuristic_extraction1}")

heuristic_extraction2 = extract_san_heuristically(res2, chess.STARTING_FEN)
print(f"Heuristic extraction from response 2: {heuristic_extraction2}")

res3 = """To determine the best move, let's analyze the given position:\n\n1. **Current Position**: \n   - White: All pawns are on the second rank. The pieces are developed with the knights, bishops, rooks, queen, and king in their starting positions or slightly moved (one knight is on e5).\n   - Black: All pawns are on the seventh rank. The pieces are mostly in their starting positions.\n\n2. **White Pieces**:\n   - Pawns: a2, b2, c2, d2, e2, f2, g2, h2\n   - Knight: b1, e5\n   - Bishop: c1, f1\n   - Rook: a1, h1\n   - Queen: d1\n   - King: e1\n\n3. **Black Pieces**:\n   - Pawns: a7, b7, c7, d7, f7, g7, h7 (missing e7 pawn)\n   - Knight: c6, g8\n   - Bishop: c8, f8\n   - Rook: a8, h8\n   - Queen: d8\n   - King: e8\n\n4. **Observation**:\n   - White has a knight on e5, which is a good central position and potentially exerts influence over the center and Black's position.\n   - Black is missing an e7 pawn, suggesting that the center might be open or that Black has played ...e6 or ...e5 at some point and then perhaps captured or lost the pawn.\n   - The presence of White's knight on e5 and the absence of Black's e7 pawn indicate potential weaknesses in Black's central control and pawn structure.\n\n5. **Evaluating Legal Moves**:\n   - The legal moves suggest that we're in a relatively early stage of the game, given the unmoved pawns and some pieces still on their starting squares.\n   - Notable moves include `Nxf7`, `Nxd7`, `Ng6`, `Nxc6`, which involve the knight on e5 capturing or moving to potentially strong or weak squares.\n\n6. **Selecting a Move**:\n   - `Nxf7` captures a pawn and puts the knight in a somewhat exposed position but could be strong depending on the follow-up.\n   - `Nxd7` also captures a pawn, and if Black recaptures with the queen or another piece, it could expose that piece to potential attacks.\n   - `Ng6` or `Ng4` puts the knight in an aggressive position but doesn't capture material.\n   - `Nxc6` captures a knight and could weaken Black's control over the center.\n\nConsidering these factors, **Nxf7** seems like a strong move as it captures a pawn. However, it's crucial to consider the potential responses and whether it puts White's knight in a vulnerable position.\n\nThe best move is **Nxf7**. This move captures a pawn and puts pressure on Black's position. It is a relatively aggressive move, aiming to gain material advantage and potentially weaken Black's position further."""

extraction3 = extract_san_heuristically(res3, "r1bqkbnr/pppp1ppp/2n5/4N3/8/8/PPPPPPPP/RNBQKB1R w KQkq - 1 3")
print("res 3:", extraction3)