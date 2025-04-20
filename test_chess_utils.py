# test_chess_utils.py

import pytest
from chess_utils import summarize_position
import chess

def test_starting_position():
    fen = chess.STARTING_FEN
    summary = summarize_position(fen)

    assert summary["fen"] == fen
    assert "K e1" in summary["white_pieces"]
    assert "k e8" in summary["black_pieces"]
    assert len(summary["legal_moves"]) == 20  # 16 pawn moves + 4 knight moves

def test_custom_position():
    fen = "8/8/8/8/8/8/8/R3K2R w KQ - 0 1"  # white can castle both sides
    summary = summarize_position(fen)

    assert "K e1" in summary["white_pieces"]
    assert "R a1" in summary["white_pieces"]
    assert "R h1" in summary["white_pieces"]
    assert "e1g1" in summary["legal_moves"]  # kingside castle
    assert "e1c1" in summary["legal_moves"]  # queenside castle

def test_illegal_position():
    with pytest.raises(ValueError):
        summarize_position("invalid_fen")

def test_empty_board():
    fen = "8/8/8/8/8/8/8/8 w - - 0 1"
    summary = summarize_position(fen)

    assert summary["white_pieces"] == []
    assert summary["black_pieces"] == []
    assert summary["legal_moves"] == []
