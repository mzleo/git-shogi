# git-shogi

## 対局データ

対局の盤面情報は `data/games.json` に保存します。

```json
[
  {
    "gameId": 1,
    "sentePlayer": "先手プレイヤー名",
    "gotePlayer": "後手プレイヤー名",
    "sfen": "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
  }
]
```

各項目の意味は次のとおりです。

- `gameId`: 対局を識別する ID
- `sentePlayer`: 先手プレイヤー名
- `gotePlayer`: 後手プレイヤー名
- `sfen`: 対局開始時点の盤面を表す SFEN 文字列

## SFEN

SFEN は、将棋の盤面を文字列で表す形式です。上の例は初期局面を表しています。

SFEN は空白区切りで、次の情報を順番に持ちます。

1. 盤面
2. 手番（`b` は先手、`w` は後手）
3. 持ち駒（`-` は持ち駒なし）
4. 手数

盤面では、大文字が先手、小文字が後手を表します。駒の記号は以下のとおりです。

| SFEN | 駒 |
| --- | --- |
| `K` / `k` | 玉 |
| `R` / `r` | 飛 |
| `B` / `b` | 角 |
| `G` / `g` | 金 |
| `S` / `s` | 銀 |
| `N` / `n` | 桂 |
| `L` / `l` | 香 |
| `P` / `p` | 歩 |

成り駒は、駒の前に `+` を付けて表します。たとえば、`+R` は龍、`+B` は馬です。

## 盤面 SVG

Pull Request が作成・更新されると、GitHub Actions が `data/games.json` の各対局を読み込み、SFEN の盤面を SVG に変換します。

生成された SVG は `generated/boards/` に保存され、Pull Request のコメントから盤面を確認できます。
