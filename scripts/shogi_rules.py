"""将棋の SFEN と基本的な合法手を扱う共通モジュール。"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


BOARD_SIZE = 9
HAND_ORDER = ("R", "B", "G", "S", "N", "L", "P")
PIECE_TYPES = frozenset(HAND_ORDER)
BOARD_PIECE_TYPES = PIECE_TYPES | {"K"}
PROMOTABLE = frozenset(("R", "B", "S", "N", "L", "P"))


@dataclass
class Position:
    """SFEN 1局面を、判定しやすいPythonのデータへ変換したもの。"""

    board: list[list[str | None]]
    turn: str
    hands: dict[str, dict[str, int]]
    move_number: int


@dataclass(frozen=True)
class Move:
    """盤上の移動または持ち駒を打つ手。"""

    from_square: tuple[int, int] | None
    to_square: tuple[int, int]
    piece: str
    promote: bool = False

    @property
    def is_drop(self) -> bool:
        return self.from_square is None


def base_piece(piece: str) -> str:
    """成り記号を除いた駒種を、大文字の SFEN 記号で返す。"""

    return piece[-1].upper()


def piece_side(piece: str) -> str:
    """駒の大文字・小文字から、先手(b)か後手(w)かを返す。"""

    return "b" if piece[-1].isupper() else "w"


def make_piece(piece_type: str, side: str, promoted: bool = False) -> str:
    """駒種と手番から SFEN の駒記号を作る。"""

    symbol = piece_type.upper() if side == "b" else piece_type.lower()
    return ("+" if promoted else "") + symbol


def parse_rank(rank: str) -> list[str | None]:
    """SFEN の1段を9マスへ展開する。

    SFEN の数字は「その数だけ空きマスが続く」という意味で、例えば
    ``3P5`` は空き3マス、歩1枚、空き5マスを表す。
    ``+`` は次の駒記号と組み合わせて成駒を表す。
    """

    cells: list[str | None] = []
    index = 0
    while index < len(rank):
        char = rank[index]
        if char.isdigit():
            count = int(char)
            if count == 0:
                raise ValueError("SFEN の空きマス数に0は使えません")
            cells.extend([None] * count)
        elif char == "+":
            index += 1
            if index >= len(rank) or rank[index].upper() not in BOARD_PIECE_TYPES:
                raise ValueError(f"不正な成駒の表記です: {rank}")
            cells.append("+" + rank[index])
        elif char.upper() in BOARD_PIECE_TYPES:
            cells.append(char)
        else:
            raise ValueError(f"不正な駒記号です: {char}")
        index += 1

    if len(cells) != BOARD_SIZE:
        raise ValueError(f"SFEN の1段は9マスである必要があります: {rank}")
    return cells


def parse_hands(hands_field: str) -> dict[str, dict[str, int]]:
    """SFEN の持ち駒欄を先手・後手ごとの個数へ変換する。"""

    hands = {"b": {piece: 0 for piece in HAND_ORDER}, "w": {piece: 0 for piece in HAND_ORDER}}
    if hands_field == "-":
        return hands

    # SFEN の持ち駒は、先手が大文字、後手が小文字で記載される。
    index = 0
    seen: set[str] = set()
    while index < len(hands_field):
        start = index
        while index < len(hands_field) and hands_field[index].isdigit():
            index += 1
        count = int(hands_field[start:index] or "1")
        if index >= len(hands_field):
            raise ValueError("持ち駒の個数の後に駒記号がありません")
        symbol = hands_field[index]
        index += 1
        if symbol.upper() not in PIECE_TYPES or symbol in seen:
            raise ValueError(f"不正な持ち駒表記です: {hands_field}")
        if count < 1:
            raise ValueError("持ち駒の個数は1以上である必要があります")
        seen.add(symbol)
        side = "b" if symbol.isupper() else "w"
        hands[side][symbol.upper()] = count
    return hands


def parse_sfen(sfen: str) -> Position:
    """SFENを盤面・手番・持ち駒・手数へ変換し、形式を検証する。"""

    # 引数なしの split は、連続した空白やタブも1つの区切りとして扱う。
    fields = sfen.split()
    if len(fields) != 4:
        raise ValueError("SFEN は盤面・手番・持ち駒・手数の4項目が必要です")

    board_field, turn, hands_field, move_number_field = fields
    if turn not in {"b", "w"}:
        raise ValueError(f"手番は b または w である必要があります: {turn}")

    try:
        move_number = int(move_number_field)
    except ValueError as error:
        raise ValueError(f"手数が整数ではありません: {move_number_field}") from error
    if move_number < 1:
        raise ValueError("手数は1以上である必要があります")

    # SFENの盤面では、"/" が段と段の区切りを表す。
    rows = board_field.split("/")
    if len(rows) != BOARD_SIZE:
        raise ValueError("SFEN の盤面は9段である必要があります")
    board = [parse_rank(row) for row in rows]

    # 将棋の対局局面として、先手・後手の玉を1枚ずつ要求する。
    if sum(piece == "K" for row in board for piece in row) != 1:
        raise ValueError("盤面には先手の玉が1枚必要です")
    if sum(piece == "k" for row in board for piece in row) != 1:
        raise ValueError("盤面には後手の玉が1枚必要です")

    return Position(board, turn, parse_hands(hands_field), move_number)


def hands_to_sfen(hands: dict[str, dict[str, int]]) -> str:
    """持ち駒をSFENの手番別表記へ戻す。"""

    result: list[str] = []
    for side, case in (("b", str.upper), ("w", str.lower)):
        for piece in HAND_ORDER:
            count = hands[side][piece]
            if count:
                result.append((str(count) if count > 1 else "") + case(piece))
    return "".join(result) or "-"


def serialize_sfen(position: Position) -> str:
    """Positionを正規化したSFEN文字列へ戻す。"""

    rows: list[str] = []
    for row in position.board:
        encoded: list[str] = []
        empty = 0
        for piece in row:
            if piece is None:
                empty += 1
                continue
            if empty:
                encoded.append(str(empty))
                empty = 0
            encoded.append(piece)
        if empty:
            encoded.append(str(empty))
        rows.append("".join(encoded))
    return (
        f"{'/'.join(rows)} {position.turn} {hands_to_sfen(position.hands)} {position.move_number}"
    )


def in_promotion_zone(side: str, row: int) -> bool:
    """指定した段が、その手番から見た敵陣3段以内かを返す。"""

    return row <= 2 if side == "b" else row >= 6


def can_promote(piece: str, from_row: int, to_row: int) -> bool:
    """移動元または移動先が敵陣なら成れる駒かを判定する。"""

    return (
        not piece.startswith("+")
        and base_piece(piece) in PROMOTABLE
        and (
            in_promotion_zone(piece_side(piece), from_row)
            or in_promotion_zone(piece_side(piece), to_row)
        )
    )


def must_promote(piece: str, to_row: int) -> bool:
    """歩・香・桂が行き所のない段へ進む場合の強制成りを判定する。"""

    if piece.startswith("+"):
        return False
    side = piece_side(piece)
    last_row = 0 if side == "b" else 8
    second_last_row = 1 if side == "b" else 7
    kind = base_piece(piece)
    return (kind in {"P", "L"} and to_row == last_row) or (
        kind == "N" and to_row in {last_row, second_last_row}
    )


def step_directions(piece: str) -> tuple[tuple[int, int], ...]:
    """駒の1マス移動方向を、先手側から見た相対方向で返す。"""

    side = piece_side(piece)
    forward = -1 if side == "b" else 1
    kind = base_piece(piece)
    if piece.startswith("+") and kind in {"S", "N", "L", "P"}:
        kind = "G"

    directions = {
        "K": ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)),
        "G": ((forward, -1), (forward, 0), (forward, 1), (0, -1), (0, 1), (-forward, 0)),
        "S": ((forward, -1), (forward, 0), (forward, 1), (-forward, -1), (-forward, 1)),
        "N": ((2 * forward, -1), (2 * forward, 1)),
        "P": ((forward, 0),),
    }
    # 龍は飛車の移動に1マスの斜め移動、馬は角の移動に1マスの縦横移動を加える。
    if piece.startswith("+") and base_piece(piece) == "R":
        return ((-1, -1), (-1, 1), (1, -1), (1, 1))
    if piece.startswith("+") and base_piece(piece) == "B":
        return ((-1, 0), (1, 0), (0, -1), (0, 1))
    if kind not in directions:
        return ()
    return directions[kind]


def slide_directions(piece: str) -> tuple[tuple[int, int], ...]:
    """飛車・角・香車のような、複数マス進める方向を返す。"""

    side = piece_side(piece)
    forward = -1 if side == "b" else 1
    kind = base_piece(piece)
    if kind == "L" and not piece.startswith("+"):
        return ((forward, 0),)
    if kind == "R":
        return ((-1, 0), (1, 0), (0, -1), (0, 1))
    if kind == "B":
        return ((-1, -1), (-1, 1), (1, -1), (1, 1))
    return ()


def inside(row: int, column: int) -> bool:
    """盤面内の座標かを判定する。"""

    return 0 <= row < BOARD_SIZE and 0 <= column < BOARD_SIZE


def _append_board_moves(position: Position, side: str, moves: list[Move]) -> None:
    """盤上の駒から、王手を無視した候補手を追加する。"""

    for row, cells in enumerate(position.board):
        for column, piece in enumerate(cells):
            if piece is None or piece_side(piece) != side:
                continue
            from_square = (row, column)

            # 1マス駒は、各方向の先頭マスだけを調べる。
            for row_delta, column_delta in step_directions(piece):
                to_row = row + row_delta
                to_column = column + column_delta
                if inside(to_row, to_column):
                    _append_move_with_promotion(
                        position, piece, from_square, (to_row, to_column), moves
                    )

            # 飛車・角・香車は、駒にぶつかるまで同じ方向へ進める。
            for row_delta, column_delta in slide_directions(piece):
                to_row = row + row_delta
                to_column = column + column_delta
                while inside(to_row, to_column):
                    target = position.board[to_row][to_column]
                    if target is not None and piece_side(target) == side:
                        break
                    _append_move_with_promotion(
                        position, piece, from_square, (to_row, to_column), moves
                    )
                    if target is not None:
                        break
                    to_row += row_delta
                    to_column += column_delta


def _append_move_with_promotion(
    position: Position,
    piece: str,
    from_square: tuple[int, int],
    to_square: tuple[int, int],
    moves: list[Move],
) -> None:
    """成り・強制成りを考慮して候補手を追加する。"""

    from_row, _ = from_square
    to_row, to_column = to_square
    target = position.board[to_row][to_column]
    if target is not None and piece_side(target) == piece_side(piece):
        return

    if must_promote(piece, to_row):
        moves.append(Move(from_square, to_square, piece, promote=True))
    else:
        moves.append(Move(from_square, to_square, piece, promote=False))
        if can_promote(piece, from_row, to_row):
            moves.append(Move(from_square, to_square, piece, promote=True))


def _has_unpromoted_pawn_on_file(position: Position, side: str, column: int) -> bool:
    """二歩判定のため、同じ筋に未成の自分の歩があるか調べる。"""

    return any(
        piece is not None
        and piece_side(piece) == side
        and base_piece(piece) == "P"
        and not piece.startswith("+")
        for row in position.board
        for piece in [row[column]]
    )


def _append_drop_moves(position: Position, side: str, moves: list[Move]) -> None:
    """持ち駒を打つ候補手を追加する。"""

    for piece_type, count in position.hands[side].items():
        if count == 0:
            continue
        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
                if position.board[row][column] is not None:
                    continue
                last_row = 0 if side == "b" else 8
                if piece_type in {"P", "L"} and row == last_row:
                    continue
                if piece_type == "N" and row in ({0, 1} if side == "b" else {7, 8}):
                    continue
                # 二歩は、同じ筋に未成の歩がある場合の駒打ちを禁止する。
                if piece_type == "P" and _has_unpromoted_pawn_on_file(position, side, column):
                    continue
                moves.append(Move(None, (row, column), make_piece(piece_type, side)))


def pseudo_legal_moves(position: Position, side: str | None = None) -> list[Move]:
    """自玉が王手かどうかを無視した候補手を列挙する。"""

    side = side or position.turn
    moves: list[Move] = []
    _append_board_moves(position, side, moves)
    _append_drop_moves(position, side, moves)
    return moves


def _find_king(position: Position, side: str) -> tuple[int, int] | None:
    target = "K" if side == "b" else "k"
    for row, cells in enumerate(position.board):
        for column, piece in enumerate(cells):
            if piece == target:
                return row, column
    return None


def is_square_attacked(position: Position, target: tuple[int, int], by_side: str) -> bool:
    """指定マスが相手の駒の攻撃範囲にあるかを判定する。"""

    return any(
        move.to_square == target
        for move in pseudo_legal_moves(position, by_side)
        if not move.is_drop
    )


def is_in_check(position: Position, side: str) -> bool:
    """指定した手番の玉が王手を受けているかを判定する。"""

    king = _find_king(position, side)
    return king is not None and is_square_attacked(position, king, "w" if side == "b" else "b")


def apply_move(position: Position, move: Move) -> Position:
    """合法性の検証後に1手を適用し、次の局面を返す。"""

    board = [row[:] for row in position.board]
    hands = {side: counts.copy() for side, counts in position.hands.items()}
    side = position.turn
    to_row, to_column = move.to_square

    if move.is_drop:
        piece_type = base_piece(move.piece)
        if hands[side][piece_type] <= 0:
            raise ValueError("持っていない駒は打てません")
        hands[side][piece_type] -= 1
        board[to_row][to_column] = make_piece(piece_type, side)
    else:
        from_row, from_column = move.from_square  # type: ignore[misc]
        moving_piece = board[from_row][from_column]
        if moving_piece is None:
            raise ValueError("移動元に駒がありません")
        captured = board[to_row][to_column]
        if captured is not None:
            captured_type = base_piece(captured)
            if captured_type != "K":
                hands[side][captured_type] += 1
        board[from_row][from_column] = None
        board[to_row][to_column] = make_piece(
            base_piece(moving_piece), side, move.promote or moving_piece.startswith("+")
        )

    return Position(board, "w" if side == "b" else "b", hands, position.move_number + 1)


def _is_pawn_drop_mate(position: Position, move: Move) -> bool:
    """歩を打いて即詰みになる「打ち歩詰め」かを判定する。"""

    if not move.is_drop or base_piece(move.piece) != "P":
        return False
    next_position = apply_move(position, move)
    opponent = next_position.turn
    return is_in_check(next_position, opponent) and not legal_moves(
        next_position, include_pawn_drop_mate=False
    )


def legal_moves(position: Position, include_pawn_drop_mate: bool = True) -> list[Move]:
    """自玉が安全で、将棋の基本ルールに違反しない手だけを列挙する。"""

    result: list[Move] = []
    for move in pseudo_legal_moves(position):
        target = position.board[move.to_square[0]][move.to_square[1]]
        # 玉を「取る」手は存在せず、王手・詰みで対局を終える。
        if target is not None and base_piece(target) == "K":
            continue
        next_position = apply_move(position, move)
        if is_in_check(next_position, position.turn):
            continue
        if include_pawn_drop_mate and _is_pawn_drop_mate(position, move):
            continue
        result.append(move)
    return result


def validate_transition(before_sfen: str, after_sfen: str) -> None:
    """2つのSFENが、合法な1手の状態遷移になっていることを検証する。"""

    before = parse_sfen(before_sfen)
    after = parse_sfen(after_sfen)
    if after.turn == before.turn:
        raise ValueError("手番が交替していません")
    if after.move_number != before.move_number + 1:
        raise ValueError("手数が1手分だけ増えていません")

    if not any(
        serialize_sfen(apply_move(before, move)) == serialize_sfen(after)
        for move in legal_moves(before)
    ):
        raise ValueError("変更後のSFENは、変更前からの合法な1手ではありません")


def square_from_notation(value: str) -> tuple[int, int]:
    """7g のような将棋座標を、SFEN配列の(row, column)へ変換する。"""

    if not re.fullmatch(r"[1-9][a-i]", value):
        raise ValueError(f"座標は1a〜9iの形式で指定してください: {value}")
    return ord(value[1]) - ord("a"), 9 - int(value[0])


def find_move(
    position: Position,
    from_square: str | None = None,
    to_square: str | None = None,
    drop_piece: str | None = None,
    promote: bool = False,
) -> Move:
    """CLI入力に一致する合法手を探す。"""

    if to_square is None:
        raise ValueError("移動先 --to は必須です")
    target = square_from_notation(to_square)
    source = square_from_notation(from_square) if from_square else None
    requested_drop = drop_piece.upper() if drop_piece else None
    if source is None and requested_drop is None:
        raise ValueError("通常の移動には --from、駒打ちには --drop が必要です")
    if source is not None and requested_drop is not None:
        raise ValueError("--from と --drop は同時に指定できません")
    candidates = [
        move
        for move in legal_moves(position)
        if move.to_square == target
        and move.from_square == source
        and (
            (
                requested_drop is not None
                and move.is_drop
                and base_piece(move.piece) == requested_drop
            )
            or (requested_drop is None and not move.is_drop)
        )
        and move.promote == promote
    ]
    if not candidates:
        raise ValueError("指定された指し手は合法手ではありません")
    return candidates[0]


def iter_changed_game_ids(before: Iterable[dict], after: Iterable[dict]) -> set[str]:
    """2つのゲーム配列から、SFENが変わった対局IDを求める。"""

    before_map = {str(game["gameId"]): str(game["sfen"]) for game in before}
    return {
        str(game["gameId"])
        for game in after
        if before_map.get(str(game["gameId"])) != str(game["sfen"])
    }
