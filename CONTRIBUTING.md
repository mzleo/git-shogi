# コントリビューションガイド

## 開発環境の準備

このリポジトリでは、Python の開発用パッケージを `pyproject.toml` で管理し、`uv.lock` でバージョンを固定しています。Python 3.10 以上を用意してください。

### uv がインストール済みか確認する

PowerShell で次のコマンドを実行します。

```powershell
uv --version
```

バージョンが表示されれば、そのまま次へ進めます。

### Windows に uv をインストールする

uv が見つからない場合は、次のいずれかの方法でインストールできます。

PowerShell の公式インストーラーを使う方法:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

または、`winget` が利用できる場合:

```powershell
winget install --id=astral-sh.uv -e
```

インストール後に PowerShell を開き直し、`uv --version` で確認してください。

Python 3.10 を uv で用意する場合は、次も実行できます。

```powershell
uv python install 3.10
```

### 依存関係をインストールする

リポジトリのルートで次を実行します。

```powershell
uv sync --locked --group dev
```

`uv.lock` に記録されたバージョンで仮想環境 `.venv` が作成され、Black、flake8、pytest などの開発用パッケージがインストールされます。

## 開発用チェック

```powershell
uv run black --check scripts tests
uv run flake8 scripts tests
uv run pytest
```

コードを編集した後は、3つのチェックがすべて成功することを確認してください。依存関係を追加・更新した場合は、`uv lock` を実行して `uv.lock` も更新します。
