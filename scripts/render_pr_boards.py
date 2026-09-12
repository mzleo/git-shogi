"""PRの直前局面と現在局面をSVGへ変換する。"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from render_shogi_board import render_svg


def _load_parent_games() -> list[dict] | None:
    """HEADの1つ前のcommitからgames.jsonを取得する。"""

    try:
        content = subprocess.check_output(
            ["git", "show", "HEAD^:data/games.json"],
            text=True,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    data = json.loads(content)
    return data if isinstance(data, list) else None


def main() -> None:
    parser = argparse.ArgumentParser(description="PRのBefore/After盤面SVGを生成します")
    parser.add_argument("--input", type=Path, default=Path("data/games.json"))
    parser.add_argument("--before", type=Path, default=Path("public/render-shogi-board-before.svg"))
    parser.add_argument("--after", type=Path, default=Path("public/render-shogi-board.svg"))
    args = parser.parse_args()

    games = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(games, list) or not games or not isinstance(games[0], dict):
        raise ValueError("games.json must contain at least one game object")

    args.after.parent.mkdir(parents=True, exist_ok=True)
    args.after.write_text(render_svg(games[0]), encoding="utf-8")

    parent_games = _load_parent_games()
    if parent_games:
        parent_by_id = {str(game["gameId"]): game for game in parent_games}
        previous = parent_by_id.get(str(games[0]["gameId"]))
        if previous:
            args.before.write_text(render_svg(previous), encoding="utf-8")
            print(args.before)
            print(args.after)
            return

    # 新しい対局の追加など、比較対象がない場合はBeforeを残さない。
    args.before.unlink(missing_ok=True)
    print(args.after)


if __name__ == "__main__":
    main()
