"""現在のJSONと直前のcommitを比較し、合法な1手かを検証する。"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from shogi_rules import parse_sfen, validate_transition


DATA_PATH = Path("data/games.json")


def _load_json(path: Path) -> list[dict]:
    """JSONが対局オブジェクトの配列になっていることを検証して読み込む。"""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(game, dict) for game in data):
        raise ValueError("games.json must contain an array of game objects")
    for game in data:
        for field in ("gameId", "sentePlayer", "gotePlayer", "sfen"):
            if field not in game:
                raise ValueError(f"必須項目がありません: {field}")
        parse_sfen(str(game["sfen"]))
    return data


def _load_parent_json() -> list[dict] | None:
    """直前commitのgames.jsonを読み込む。新規追加時はNoneを返す。"""

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
    current = _load_json(DATA_PATH)
    parent = _load_parent_json()
    if parent is None:
        print("直前のgames.jsonがないため、SFEN形式のみ検証しました")
        return

    previous_by_id = {str(game["gameId"]): game for game in parent}
    for game in current:
        previous = previous_by_id.get(str(game["gameId"]))
        if previous is None:
            continue
        if str(previous["sfen"]) == str(game["sfen"]):
            continue
        validate_transition(str(previous["sfen"]), str(game["sfen"]))
        print(f"gameId={game['gameId']}: 合法な1手として検証しました")


if __name__ == "__main__":
    main()
