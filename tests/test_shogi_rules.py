"""将棋ルールとSFEN変換のテスト。"""

from __future__ import annotations

import pytest

from shogi_rules import (
    apply_move,
    find_move,
    is_in_check,
    legal_moves,
    parse_sfen,
    serialize_sfen,
    validate_transition,
)


INITIAL_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"


def test_initial_sfen_round_trips() -> None:
    assert serialize_sfen(parse_sfen(INITIAL_SFEN)) == INITIAL_SFEN


def test_normal_pawn_move_updates_turn_and_move_number() -> None:
    position = parse_sfen(INITIAL_SFEN)
    move = find_move(position, from_square="7g", to_square="7f")

    after = apply_move(position, move)

    assert serialize_sfen(after) == (
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL w - 2"
    )


def test_blocked_rook_cannot_move_through_a_pawn() -> None:
    position = parse_sfen(INITIAL_SFEN)

    with pytest.raises(ValueError):
        find_move(position, from_square="2h", to_square="2g")


def test_nifu_forbids_pawn_drop_on_a_file_with_an_unpromoted_pawn() -> None:
    sfen = "4k4/9/9/9/9/9/4P4/9/4K4 b P 1"
    position = parse_sfen(sfen)

    drops = [move for move in legal_moves(position) if move.is_drop]

    assert all(move.to_square[1] != 4 for move in drops)


def test_last_rank_pawn_move_requires_promotion() -> None:
    position = parse_sfen("4k4/P8/9/9/9/9/9/9/4K4 b - 1")

    with pytest.raises(ValueError):
        find_move(position, from_square="9b", to_square="9a")

    promoted = find_move(position, from_square="9b", to_square="9a", promote=True)
    assert serialize_sfen(apply_move(position, promoted)).startswith("+P3k4/")


def test_hands_are_parsed_and_serialized() -> None:
    sfen = "4k4/9/9/9/9/9/9/9/4K4 b R2Pr 1"
    assert serialize_sfen(parse_sfen(sfen)) == sfen


def test_capture_adds_the_captured_piece_to_the_hand() -> None:
    position = parse_sfen("4k4/9/9/9/4R1p2/9/9/9/4K4 b - 1")
    move = find_move(position, from_square="5e", to_square="3e")

    after = apply_move(position, move)

    assert after.board[4][6] == "R"
    assert after.hands["b"]["P"] == 1


def test_hand_drop_consumes_the_piece() -> None:
    position = parse_sfen("4k4/9/9/9/9/9/9/9/4K4 b P 1")
    move = find_move(position, to_square="5e", drop_piece="P")

    after = apply_move(position, move)

    assert after.board[4][4] == "P"
    assert after.hands["b"]["P"] == 0


def test_transition_accepts_one_legal_move() -> None:
    after_sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL w - 2"

    validate_transition(INITIAL_SFEN, after_sfen)


def test_self_check_is_not_a_legal_move() -> None:
    sfen = "4k4/9/9/9/9/9/9/4r4/4K3P b - 1"
    position = parse_sfen(sfen)

    assert is_in_check(position, "b")
    assert all(move.from_square != (8, 8) for move in legal_moves(position))


def test_checkmate_has_no_legal_moves() -> None:
    sfen = "Kr7/1k7/9/9/9/9/9/9/9 b - 1"
    position = parse_sfen(sfen)

    assert is_in_check(position, "b")
    assert legal_moves(position) == []
