"""SVG生成のテスト。"""

from __future__ import annotations

from render_shogi_board import piece_label, render_svg


def test_promoted_piece_labels_are_rendered_in_japanese() -> None:
    assert piece_label("+R") == "龍"
    assert piece_label("+B") == "馬"
    assert piece_label("+P") == "と"


def test_svg_contains_hands_and_promoted_pieces() -> None:
    game = {
        "gameId": 2,
        "sentePlayer": "Alice",
        "gotePlayer": "Bob",
        "sfen": "4k4/9/9/3+R5/9/9/9/9/4K4 b R2p 12",
    }

    svg = render_svg(game)

    assert "先手の持ち駒" in svg
    assert "飛×1" in svg
    assert "後手の持ち駒" in svg
    assert "歩×2" in svg
    assert ">龍</text>" in svg
