# プロジェクト構造

このプロジェクトは、PyPIパッケージとサンプルプロジェクトの両方を含んでいます。

## ディレクトリ構成

```
.
├── src/
│   └── pytest_bdd_md_report/      # PyPIパッケージ（配布対象）
│       ├── __init__.py                  # パッケージメタデータ
│       ├── plugin.py                    # pytestプラグイン本体
│       └── templates/
│           └── default_report.md.j2     # デフォルトテンプレート
│
├── app/                                 # サンプルWebアプリ（配布対象外）
│   ├── server.py                        # Flaskサーバー
│   ├── login.html                       # ログインページ
│   └── dashboard.html                   # ダッシュボード
│
├── tests/                               # サンプルテスト（配布対象外）
│   ├── features/                        # Gherkinシナリオ
│   │   └── login.feature
│   ├── steps/                           # ステップ定義
│   │   ├── __init__.py
│   │   └── login_steps.py
│   ├── conftest.py                      # pytest設定
│   └── test_login.py                    # テストファイル
│
├── dist/                                # ビルド成果物
│   ├── pytest_bdd_md_report-1.0.0-py3-none-any.whl
│   └── pytest_bdd_md_report-1.0.0.tar.gz
│
├── pyproject.toml                       # パッケージ設定
├── LICENSE                              # MITライセンス
├── README.md                            # パッケージ説明（PyPIで表示）
├── EXAMPLE.md                           # サンプルプロジェクトの説明
├── QUICKSTART.md                        # 導入ガイド
└── PUBLISHING.md                        # PyPI公開手順
```

## 配布パッケージの内容

`uv build` でビルドされるwhlファイルには、以下のみが含まれます：

```
pytest_bdd_md_report/
├── __init__.py
├── plugin.py
└── templates/
    └── default_report.md.j2
```

**除外されるもの:**
- `app/` - サンプルWebアプリ
- `tests/` - サンプルテスト
- `.git/`, `.venv/`, `.idea/` - 開発環境ファイル

## 各ファイルの役割

### パッケージコア（src/pytest_bdd_md_report/）

| ファイル | 役割 |
|---------|------|
| `__init__.py` | パッケージバージョン情報 |
| `plugin.py` | pytestプラグイン実装（フック、レポート生成ロジック） |
| `templates/default_report.md.j2` | Jinja2テンプレート（デフォルトレポート形式） |

### サンプルアプリ（app/）

| ファイル | 役割 |
|---------|------|
| `server.py` | Flask開発サーバー（localhost:8000） |
| `login.html` | ログインページ（テスト対象） |
| `dashboard.html` | ダッシュボード（ログイン成功後） |

### サンプルテスト（tests/）

| ファイル | 役割 |
|---------|------|
| `features/login.feature` | Gherkinシナリオ（BDD形式） |
| `steps/login_steps.py` | ステップ定義（Playwrightでブラウザ操作） |
| `conftest.py` | pytestプラグイン設定 |
| `test_login.py` | テストエントリポイント |

### ドキュメント

| ファイル | 役割 |
|---------|------|
| `README.md` | パッケージ説明（PyPI表示用） |
| `EXAMPLE.md` | サンプルプロジェクトの詳細説明 |
| `QUICKSTART.md` | 他プロジェクトへの導入手順 |
| `PUBLISHING.md` | PyPI公開手順 |
| `PROJECT_STRUCTURE.md` | このファイル（プロジェクト構造説明） |

### 設定ファイル

| ファイル | 役割 |
|---------|------|
| `pyproject.toml` | パッケージメタデータ、ビルド設定、依存関係 |
| `LICENSE` | MITライセンス |
| `.gitignore` | Git除外設定 |
| `uv.lock` | uv依存関係ロックファイル |

## パッケージのビルドとインストール

### ローカルビルド

```bash
uv build
```

### ローカルインストール（開発用）

```bash
# 編集可能モードでインストール
uv pip install -e .
```

### PyPIからインストール（公開後）

```bash
pip install pytest-bdd-md-report
```

## 開発ワークフロー

1. **パッケージコード編集**: `src/pytest_bdd_md_report/plugin.py`
2. **サンプルでテスト**: `uv run pytest tests/ --markdown-report=test_report.md`
3. **ビルド**: `uv build`
4. **whl内容確認**: `unzip -l dist/*.whl`
5. **公開**: `twine upload dist/*`

## サンプルアプリの実行方法

```bash
# Webサーバー起動
uv run python app/server.py

# 別ターミナルでテスト実行
uv run pytest tests/ --markdown-report=test_report.md --markdown-report-verbose
```

## CI/CD統合

GitHub Actionsでの自動ビルド・公開例は `PUBLISHING.md` を参照してください。
