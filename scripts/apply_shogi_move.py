"""座標を指定して、data/games.json の1局面へ合法な1手を適用するCLI。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from shogi_rules import apply_move, find_move, parse_sfen, serialize_sfen


def main() -> None:
    parser = argparse.ArgumentParser(description="座標指定で将棋の1手を適用します")
    parser.add_argument("--input", type=Path, default=Path("data/games.json"))
    parser.add_argument("--game-id", required=True, help="更新する対局ID")
    parser.add_argument("--from", dest="from_square", help="移動元（例: 7g）")
    parser.add_argument("--to", required=True, help="移動先（例: 7f）")
    parser.add_argument("--drop", help="駒打ちの場合の駒（例: P, R）")
    parser.add_argument("--promote", action="store_true", help="移動時に成る")
    args = parser.parse_args()

    games = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(games, list):
        raise ValueError("games.json must contain an array")

    for game in games:
        if str(game.get("gameId")) != str(args.game_id):
            continue
        position = parse_sfen(str(game["sfen"]))
        move = find_move(position, args.from_square, args.to, args.drop, args.promote)
        game["sfen"] = serialize_sfen(apply_move(position, move))
        args.input.write_text(
            json.dumps(games, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(game["sfen"])
        return

    raise ValueError(f"指定された対局IDが見つかりません: {args.game_id}")


if __name__ == "__main__":
    main()
