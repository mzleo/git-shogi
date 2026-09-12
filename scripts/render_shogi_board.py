"""Render the shogi position stored in data/games.json as an SVG file."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


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

BOARD_SIZE = 9
CELL_SIZE = 72
BOARD_X = 80
BOARD_Y = 64
BOARD_WIDTH = BOARD_SIZE * CELL_SIZE
SVG_WIDTH = BOARD_X * 2 + BOARD_WIDTH
SVG_HEIGHT = BOARD_Y * 2 + BOARD_WIDTH


def parse_board(sfen: str) -> tuple[list[list[str | None]], str, str, int]:
    fields = sfen.split()
    if len(fields) != 4:
        raise ValueError("SFEN must contain four space-separated fields")

    board_field, turn, hands, move_number = fields
    if turn not in {"b", "w"}:
        raise ValueError(f"Unsupported SFEN turn: {turn}")
    if hands != "-":
        raise ValueError("Hand pieces are not supported yet")
    try:
        move = int(move_number)
    except ValueError as error:
        raise ValueError(f"Invalid SFEN move number: {move_number}") from error

    rows = board_field.split("/")
    if len(rows) != BOARD_SIZE:
        raise ValueError("SFEN board must contain nine ranks")

    board: list[list[str | None]] = []
    for row in rows:
        cells: list[str | None] = []
        index = 0
        while index < len(row):
            char = row[index]
            if char.isdigit():
                cells.extend([None] * int(char))
            elif char == "+":
                index += 1
                if index >= len(row) or row[index].upper() not in PIECE_NAMES:
                    raise ValueError(f"Invalid promoted piece in SFEN row: {row}")
                cells.append("+" + row[index])
            elif char.upper() in PIECE_NAMES:
                cells.append(char)
            else:
                raise ValueError(f"Invalid piece in SFEN row: {row}")
            index += 1
        if len(cells) != BOARD_SIZE:
            raise ValueError(f"SFEN row must contain nine squares: {row}")
        board.append(cells)
    return board, turn, hands, move


def piece_label(piece: str) -> str:
    if piece.startswith("+"):
        return PROMOTED_PIECE_NAMES[piece[-1].upper()]
    return PIECE_NAMES[piece[-1].upper()]


def render_svg(game: dict) -> str:
    game_id = html.escape(str(game["gameId"]))
    sente = html.escape(str(game["sentePlayer"]))
    gote = html.escape(str(game["gotePlayer"]))
    board, turn, _, move_number = parse_board(str(game["sfen"]))

    svg: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" '
        f'height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">',
        '<title>Shogi game ' + game_id + '</title>',
        '<rect width="100%" height="100%" fill="#f7e5b5"/>',
        f'<text x="{BOARD_X}" y="28" font-family="sans-serif" '
        f'font-size="20" font-weight="bold">Game {game_id}</text>',
        f'<text x="{BOARD_X}" y="52" font-family="sans-serif" font-size="16">'
        f'Sente: {sente} / Gote: {gote} / Turn: {turn} / Move: {move_number}</text>',
        f'<rect x="{BOARD_X}" y="{BOARD_Y}" width="{BOARD_WIDTH}" '
        f'height="{BOARD_WIDTH}" fill="#e8c77d" stroke="#49351f" stroke-width="3"/>',
    ]

    for index in range(BOARD_SIZE + 1):
        position = BOARD_X + index * CELL_SIZE
        svg.append(f'<path d="M {position} {BOARD_Y} V {BOARD_Y + BOARD_WIDTH}" '
                   'stroke="#49351f" stroke-width="1"/>')
        position = BOARD_Y + index * CELL_SIZE
        svg.append(f'<path d="M {BOARD_X} {position} H {BOARD_X + BOARD_WIDTH}" '
                   'stroke="#49351f" stroke-width="1"/>')

    for row, cells in enumerate(board):
        for column, piece in enumerate(cells):
            if piece is None:
                continue
            x = BOARD_X + column * CELL_SIZE + CELL_SIZE / 2
            y = BOARD_Y + row * CELL_SIZE + CELL_SIZE / 2
            fill = "#fff8df" if piece[-1].isupper() else "#d8e8ff"
            transform = " rotate(180 {x} {y})" if piece[-1].islower() else ""
            label = html.escape(piece_label(piece))
            svg.append(
                f'<g transform="{transform.format(x=x, y=y)}">'
                f'<path d="M {x - 25} {y - 30} L {x + 25} {y - 30} '
                f'L {x + 29} {y + 30} L {x - 29} {y + 30} Z" '
                f'fill="{fill}" stroke="#49351f" stroke-width="2"/>'
                f'<text x="{x}" y="{y + 10}" text-anchor="middle" '
                f'font-family="serif" font-size="28" font-weight="bold">'
                f'{label}</text></g>'
            )

    svg.append("</svg>")
    return "\n".join(svg) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/games.json"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("public/render-shogi-board.svg"),
        help="SVG output path (the first game in the JSON array is rendered)",
    )
    args = parser.parse_args()

    games = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(games, list):
        raise ValueError("games.json must contain an array")
    if not games:
        raise ValueError("games.json must contain at least one game")

    if not isinstance(games[0], dict):
        raise ValueError("Each game must be a JSON object")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_svg(games[0]), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
