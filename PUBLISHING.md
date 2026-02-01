# PyPI公開手順

## 事前準備

### 1. PyPIアカウント作成

- 本番環境: https://pypi.org/account/register/
- テスト環境: https://test.pypi.org/account/register/

### 2. API トークン取得

1. PyPIにログイン
2. Account settings → API tokens
3. "Add API token" をクリック
4. Scope: "Entire account" または特定プロジェクトを選択
5. 生成されたトークンを保存（`pypi-` で始まる文字列）

### 3. 認証情報設定

```bash
# ~/.pypirc に保存（推奨しない）
# または環境変数で設定（推奨）
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here
```

## ビルド

### ローカルビルド

```bash
# 依存関係をインストール
uv add hatchling --dev

# ビルド実行
uv build

# 生成されるファイル
# - dist/pytest_bdd_md_report-1.0.0.tar.gz (source distribution)
# - dist/pytest_bdd_md_report-1.0.0-py3-none-any.whl (wheel)
```

### ビルド内容の確認

```bash
# wheelファイルの内容を確認
unzip -l dist/pytest_bdd_md_report-1.0.0-py3-none-any.whl

# サンプルアプリやテストが含まれていないことを確認
# - app/ は含まれない
# - tests/ は含まれない
# - src/pytest_bdd_md_report/ のみが含まれる
```

## テスト公開（TestPyPI）

本番環境に公開する前に、テスト環境で動作確認することを推奨します。

```bash
# twineをインストール
pip install twine

# TestPyPIにアップロード
twine upload --repository testpypi dist/*

# TestPyPIからインストールしてテスト
pip install --index-url https://test.pypi.org/simple/ pytest-bdd-md-report
```

## 本番公開（PyPI）

### バージョン更新

`src/pytest_bdd_md_report/__init__.py` と `pyproject.toml` のバージョンを更新：

```python
# __init__.py
__version__ = "1.0.1"
```

```toml
# pyproject.toml
[project]
version = "1.0.1"
```

### アップロード

```bash
# 古いビルド成果物を削除
rm -rf dist/

# 再ビルド, アップロード
source .venv/bin/activate; uv build; twine upload dist/*
```

### 公開確認

```bash
# PyPIからインストールしてテスト
pip install pytest-bdd-md-report

# バージョン確認
python -c "import pytest_bdd_md_report; print(pytest_bdd_md_report.__version__)"
```

## GitHub Actions による自動公開（推奨）

`.github/workflows/publish.yml` を作成して、タグpush時に自動公開：

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install hatchling twine

      - name: Build
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

GitHub Secretsに `PYPI_API_TOKEN` を登録してから使用します。

## リリースワークフロー

1. バージョン番号を更新（`__init__.py`, `pyproject.toml`）
2. CHANGELOG.md を更新
3. コミット & プッシュ
4. Gitタグを作成: `git tag v1.0.1 && git push origin v1.0.1`
5. GitHub Actionsが自動でビルド & 公開

## トラブルシューティング

### エラー: "File already exists"

PyPIでは同じバージョン番号を再アップロードできません。バージョン番号を上げてください。

### エラー: "Invalid distribution"

```bash
# メタデータの検証
twine check dist/*
```

### エラー: "403 Forbidden"

APIトークンが正しいか確認してください。トークンには `pypi-` プレフィックスが必要です。
