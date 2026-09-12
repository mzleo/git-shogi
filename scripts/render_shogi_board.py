"""data/games.json の SFEN を、盤面と持ち駒を含む SVG に変換する。"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from shogi_rules import Position, hands_to_sfen, parse_sfen


PIECE_NAMES = {
    "K": "玉",
    "R": "飛",
    "B": "角",
    "G": "金",
    "S": "銀",
    "N": "桂",
    "L": "香",
    "P": "歩",
}

PROMOTED_PIECE_NAMES = {
    "R": "龍",
    "B": "馬",
    "S": "全",
    "N": "圭",
    "L": "杏",
    "P": "と",
}

# 将棋盤は9×9マス。盤面の左右には先手・後手の持ち駒を表示する。
BOARD_SIZE = 9
CELL_SIZE = 72
BOARD_X = 240
BOARD_Y = 112
BOARD_WIDTH = BOARD_SIZE * CELL_SIZE
SVG_WIDTH = BOARD_X + BOARD_WIDTH + 240
SVG_HEIGHT = BOARD_Y + BOARD_WIDTH + 32


def parse_board(sfen: str) -> tuple[list[list[str | None]], str, str, int]:
    """既存の呼び出し向けに、SFENを盤面情報へ分解して返す。"""

    position = parse_sfen(sfen)
    return position.board, position.turn, hands_to_sfen(position.hands), position.move_number


def piece_label(piece: str) -> str:
    """SFENの駒記号をSVGに表示する日本語名へ変換する。"""

    piece_type = piece[-1].upper()
    if piece.startswith("+"):
        return PROMOTED_PIECE_NAMES[piece_type]
    return PIECE_NAMES[piece_type]


def _hands_label(position: Position, side: str) -> str:
    """持ち駒を「飛×1、歩×2」のような表示文字列へ変換する。"""

    labels: list[str] = []
    for piece_type, count in position.hands[side].items():
        if count:
            labels.append(f"{PIECE_NAMES[piece_type]}×{count}")
    return "、".join(labels) or "なし"


def _append_hand_area(svg: list[str], position: Position) -> None:
    """盤面の左右に先手・後手の持ち駒を描画する。"""

    areas = (
        (24, "先手の持ち駒", "b"),
        (BOARD_X + BOARD_WIDTH + 24, "後手の持ち駒", "w"),
    )
    for x, title, side in areas:
        svg.append(
            f'<text x="{x}" y="{BOARD_Y + 28}" font-family="sans-serif" '
            f'font-size="18" font-weight="bold">{title}</text>'
        )
        svg.append(
            f'<text x="{x}" y="{BOARD_Y + 60}" font-family="sans-serif" '
            f'font-size="16">{html.escape(_hands_label(position, side))}</text>'
        )


def render_svg(game: dict) -> str:
    """1件の対局データから将棋盤SVGの文字列を作る。"""

    # 対局者名などの入力値をSVGへ埋め込むため、XMLの特殊文字をエスケープする。
    game_id = html.escape(str(game["gameId"]))
    sente = html.escape(str(game["sentePlayer"]))
    gote = html.escape(str(game["gotePlayer"]))
    position = parse_sfen(str(game["sfen"]))

    # SVGのルート要素、タイトル、対局情報、盤面の背景を用意する。
    svg: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" '
        f'height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">',
        f"<title>Shogi game {game_id}</title>",
        '<rect width="100%" height="100%" fill="#f7e5b5"/>',
        f'<text x="{BOARD_X}" y="28" text-anchor="middle" font-family="sans-serif" '
        f'font-size="20" font-weight="bold">Game {game_id}</text>',
        f'<text x="{BOARD_X}" y="56" text-anchor="middle" font-family="sans-serif" '
        f'font-size="16">Sente: {sente} / Gote: {gote} / '
        f'Turn: {"Sente" if position.turn == "b" else "Gote"} / '
        f"Move: {position.move_number}</text>",
        f'<rect x="{BOARD_X}" y="{BOARD_Y}" width="{BOARD_WIDTH}" '
        f'height="{BOARD_WIDTH}" fill="#e8c77d" stroke="#49351f" stroke-width="3"/>',
    ]
    _append_hand_area(svg, position)

    # 盤面の縦線・横線を描画して9×9のマス目を作る。
    for index in range(BOARD_SIZE + 1):
        x = BOARD_X + index * CELL_SIZE
        y = BOARD_Y + index * CELL_SIZE
        svg.append(f'<path d="M {x} {BOARD_Y} V {BOARD_Y + BOARD_WIDTH}" stroke="#49351f"/>')
        svg.append(f'<path d="M {BOARD_X} {y} H {BOARD_X + BOARD_WIDTH}" stroke="#49351f"/>')

    # SFENを変換した2次元配列を走査し、駒があるマスだけ描画する。
    for row, cells in enumerate(position.board):
        for column, piece in enumerate(cells):
            if piece is None:
                continue
            x = BOARD_X + column * CELL_SIZE + CELL_SIZE / 2
            y = BOARD_Y + row * CELL_SIZE + CELL_SIZE / 2
            # SFENの小文字は後手の駒なので、後手側から見えるよう180度回転する。
            transform = f' transform="rotate(180 {x} {y})"' if piece[-1].islower() else ""
            label = html.escape(piece_label(piece))
            fill = "#fff8df" if piece[-1].isupper() else "#d8e8ff"
            svg.append(
                f"<g{transform}>"
                f'<path d="M {x - 25} {y - 30} L {x + 25} {y - 30} '
                f'L {x + 29} {y + 30} L {x - 29} {y + 30} Z" '
                f'fill="{fill}" stroke="#49351f" stroke-width="2"/>'
                f'<text x="{x}" y="{y + 10}" text-anchor="middle" '
                f'font-family="serif" font-size="28" font-weight="bold">{label}</text></g>'
            )

    svg.append("</svg>")
    return "\n".join(svg) + "\n"


def main() -> None:
    """JSONの先頭データをSVGへ出力する。"""

    parser = argparse.ArgumentParser(description="SFENから将棋盤SVGを生成します")
    parser.add_argument("--input", type=Path, default=Path("data/games.json"))
    parser.add_argument("--output", type=Path, default=Path("public/render-shogi-board.svg"))
    args = parser.parse_args()

    games = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(games, list) or not games:
        raise ValueError("games.json must contain at least one game")
    if not isinstance(games[0], dict):
        raise ValueError("Each game must be a JSON object")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_svg(games[0]), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
