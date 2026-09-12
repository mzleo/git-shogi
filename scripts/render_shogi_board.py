"""data/games.json の SFEN を将棋盤の SVG ファイルに変換するスクリプト。"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


# SFEN では、先手の駒を大文字、後手の駒を小文字で表す。
# ここでは大文字にそろえた駒記号をキーにして、日本語の駒名へ変換する。
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

# 成駒は SFEN 上では駒の前に "+" を付けて表す。
# 例えば "+R" は成った飛車（龍）を意味する。
PROMOTED_PIECE_NAMES = {
    "R": "龍",
    "B": "馬",
    "S": "全",
    "N": "圭",
    "L": "杏",
    "P": "と",
}

# 将棋盤は 9×9 マス。SVG 上では1マスを CELL_SIZE pxとして描画する。
BOARD_SIZE = 9
CELL_SIZE = 72

# 盤面の左上にタイトルや対局情報を表示するための余白。
BOARD_X = 80
BOARD_Y = 64
BOARD_WIDTH = BOARD_SIZE * CELL_SIZE
SVG_WIDTH = BOARD_X * 2 + BOARD_WIDTH
SVG_HEIGHT = BOARD_Y * 2 + BOARD_WIDTH


def parse_board(sfen: str) -> tuple[list[list[str | None]], str, str, int]:
    """SFEN を盤面・手番・持ち駒・手数に分解する。

    SFEN は次の4項目を空白で区切って表す。
    1. 盤面
    2. 手番（b=先手、w=後手）
    3. 持ち駒（- は持ち駒なし）
    4. 手数
    """
    # 引数なしの split は、連続した空白やタブもまとめて区切りとして扱う。
    fields = sfen.split()
    if len(fields) != 4:
        raise ValueError("SFEN must contain four space-separated fields")

    board_field, turn, hands, move_number = fields

    # 手番は b（black / 先手）か w（white / 後手）でなければならない。
    if turn not in {"b", "w"}:
        raise ValueError(f"Unsupported SFEN turn: {turn}")

    # 現在は盤上の駒だけを描画し、持ち駒の描画には対応していない。
    if hands != "-":
        raise ValueError("Hand pieces are not supported yet")

    # SFEN の最後の数字は、現在の手数を表す。
    try:
        move = int(move_number)
    except ValueError as error:
        raise ValueError(f"Invalid SFEN move number: {move_number}") from error

    # SFEN の盤面は、9段分を "/" で区切って表す。
    # 1つ目が盤面の上段、9つ目が盤面の下段に対応する。
    rows = board_field.split("/")
    if len(rows) != BOARD_SIZE:
        raise ValueError("SFEN board must contain nine ranks")

    board: list[list[str | None]] = []
    for row in rows:
        cells: list[str | None] = []
        index = 0
        while index < len(row):
            char = row[index]

            # 数字は、その数だけ空きマスが連続していることを表す。
            # 例えば "3P5" は、空き3マス・歩1枚・空き5マス。
            if char.isdigit():
                cells.extend([None] * int(char))

            # "+" は成駒の開始記号。次の1文字と組み合わせて "+R" などにする。
            elif char == "+":
                index += 1
                if index >= len(row) or row[index].upper() not in PIECE_NAMES:
                    raise ValueError(f"Invalid promoted piece in SFEN row: {row}")
                cells.append("+" + row[index])

            # 通常の駒記号。大文字なら先手、小文字なら後手の駒になる。
            elif char.upper() in PIECE_NAMES:
                cells.append(char)
            else:
                raise ValueError(f"Invalid piece in SFEN row: {row}")
            index += 1
        # 1段は必ず9マス分でなければならない。
        if len(cells) != BOARD_SIZE:
            raise ValueError(f"SFEN row must contain nine squares: {row}")
        board.append(cells)
    return board, turn, hands, move


def piece_label(piece: str) -> str:
    """SFEN の駒記号を SVG に表示する日本語名へ変換する。"""
    if piece.startswith("+"):
        return PROMOTED_PIECE_NAMES[piece[-1].upper()]
    return PIECE_NAMES[piece[-1].upper()]


def render_svg(game: dict) -> str:
    """1件の対局データから将棋盤 SVG の文字列を作る。"""
    # ユーザー入力を SVG のテキストへ埋め込むため、特殊文字をエスケープする。
    game_id = html.escape(str(game["gameId"]))
    sente = html.escape(str(game["sentePlayer"]))
    gote = html.escape(str(game["gotePlayer"]))
    board, turn, _, move_number = parse_board(str(game["sfen"]))

    # SVG は XML 形式のため、まずルート要素と盤面の背景を用意する。
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

    # 縦線・横線をそれぞれ10本ずつ描画し、9×9の盤面を作る。
    for index in range(BOARD_SIZE + 1):
        position = BOARD_X + index * CELL_SIZE
        svg.append(f'<path d="M {position} {BOARD_Y} V {BOARD_Y + BOARD_WIDTH}" '
                   'stroke="#49351f" stroke-width="1"/>')
        position = BOARD_Y + index * CELL_SIZE
        svg.append(f'<path d="M {BOARD_X} {position} H {BOARD_X + BOARD_WIDTH}" '
                   'stroke="#49351f" stroke-width="1"/>')

    # SFEN を変換した2次元配列を走査し、駒があるマスだけSVGへ追加する。
    for row, cells in enumerate(board):
        for column, piece in enumerate(cells):
            if piece is None:
                continue
            x = BOARD_X + column * CELL_SIZE + CELL_SIZE / 2
            y = BOARD_Y + row * CELL_SIZE + CELL_SIZE / 2
            # SFEN の大文字は先手、小文字は後手。後手の駒は180度回転させる。
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

    # すべての要素を追加したら、SVG のルート要素を閉じる。
    svg.append("</svg>")
    return "\n".join(svg) + "\n"


def main() -> None:
    """コマンドライン引数を受け取り、JSON の先頭データを SVG に出力する。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/games.json"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("public/render-shogi-board.svg"),
        help="SVG output path (the first game in the JSON array is rendered)",
    )
    args = parser.parse_args()

    # JSON ファイルを読み込み、対局データの配列であることを確認する。
    games = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(games, list):
        raise ValueError("games.json must contain an array")
    if not games:
        raise ValueError("games.json must contain at least one game")

    if not isinstance(games[0], dict):
        raise ValueError("Each game must be a JSON object")

    # 出力先の親ディレクトリ（通常は public/）がなければ作成する。
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_svg(games[0]), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
