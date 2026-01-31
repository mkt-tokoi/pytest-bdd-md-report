# DSL-Driven E2E Testing - サンプルプロジェクト

このリポジトリには以下が含まれています：

1. **pytest-bdd-md-report** - PyPIパッケージ（`src/` ディレクトリ）
2. **サンプルE2Eテストプロジェクト** - 使用例（`app/`, `tests/` ディレクトリ）

このファイルは **サンプルプロジェクト** の説明です。パッケージの使い方は [README.md](README.md) または [QUICKSTART.md](QUICKSTART.md) を参照してください。

---

## サンプルプロジェクトについて

Python + pytest-bdd + pytest-playwright + **pytest-bdd-md-report** を使用した DSL 駆動の E2E テストのサンプル実装です。

## 環境セットアップ

### 1. 依存パッケージのインストール

```bash
# uvの場合
uv add pytest pytest-bdd pytest-playwright pytest-bdd-md-report

# pipの場合
pip install pytest pytest-bdd pytest-playwright pytest-bdd-md-report

# Playwrightブラウザのインストール
playwright install chromium
```

## サンプルプロジェクト構成

```
project-root/
├─ src/                         # PyPIパッケージ（pytest-bdd-md-report）
│  └─ pytest_bdd_md_report/
│     ├─ plugin.py
│     └─ templates/
│        └─ default_report.md.j2
├─ app/                         # サンプルWebアプリ
│  ├─ login.html                # サンプルログインページ
│  ├─ dashboard.html            # サンプルダッシュボード
│  └─ server.py                 # 開発用 HTTP サーバー
├─ tests/                       # サンプルテスト
│  ├─ features/
│  │  └─ login.feature          # Gherkin DSL テストシナリオ
│  ├─ steps/
│  │  └─ login_steps.py         # ステップ定義（Playwright 実装）
│  ├─ conftest.py               # pytest 設定
│  └─ test_login.py             # pytest エントリポイント
├─ pyproject.toml
└─ README.md
```

**注意:** `pytest-bdd-md-report` パッケージは `src/` ディレクトリにあり、PyPIパッケージとして独立しています。サンプルテストでは、インストール済みのパッケージを使用します。

## テストの実行方法

### 1. サンプルアプリケーションの起動

別のターミナルでサーバーを起動します：

```bash
# uvの場合
uv run python app/server.py

# 直接実行の場合
python app/server.py
```

サーバーは http://localhost:8000/ で起動します。

### 2. テストの実行

#### 通常実行（ヘッドレスモード）

```bash
# uvの場合
uv run pytest

# 直接実行の場合
pytest
```

#### ブラウザを表示して実行

```bash
uv run pytest --headed
```

#### トレース取得（デバッグ用）

```bash
uv run pytest --tracing=on
```

#### 詳細な出力

```bash
uv run pytest -v -s
```

## Markdownレポート機能

テスト結果をMarkdown形式でレポート出力する機能を提供します。

### 基本的な使い方

```bash
# Markdownレポートを生成
pytest --markdown-report=test_report.md

# 詳細なステップ情報を含める（Given/When/Then）
pytest --markdown-report=test_report.md --markdown-report-verbose

# カスタムテンプレートを使用
pytest --markdown-report=test_report.md --markdown-report-template=custom.md.j2

# 失敗時のスクリーンショットを含める
pytest --markdown-report=test_report.md --markdown-report-screenshots --screenshot=only-on-failure
```

### CLIオプション

| オプション | 説明 |
|-----------|------|
| `--markdown-report=path` | Markdownレポートの出力パス（指定しない場合はレポートを生成しない） |
| `--markdown-report-verbose` | 詳細なステップ情報（Given/When/Then）を含める |
| `--markdown-report-template=path` | カスタムJinja2テンプレートファイルのパス |
| `--markdown-report-screenshots` | 失敗時のスクリーンショットをレポートに埋め込む |
| `--markdown-report-embed-images` | スクリーンショットをBase64エンコードして直接埋め込む |

### 出力例

#### 通常モード

```markdown
## Summary
- **Total Tests**: 1
- **Passed**: 1
- **Failed**: 0

## Test Results

### Feature: ログイン機能

#### Scenario: 正常にログインできる
- **Status**: PASSED
- **Duration**: 1.73s
```

#### 詳細モード（`--markdown-report-verbose`）

```markdown
#### Scenario: 正常にログインできる
- **Status**: PASSED
- **Duration**: 1.73s

**Steps:**
1. Given ログインページを開いている (0.45s)
2. When 正しいユーザー情報を入力する (0.98s)
3. Then ダッシュボードが表示される (0.30s)
```

### カスタムテンプレート

Jinja2テンプレートを使用してレポートフォーマットをカスタマイズできます。

#### テンプレート変数

| 変数 | 型 | 説明 |
|------|-----|------|
| `generation_time` | str | レポート生成時刻 |
| `summary.total_tests` | int | 総テスト数 |
| `summary.passed` | int | 成功数 |
| `summary.failed` | int | 失敗数 |
| `summary.skipped` | int | スキップ数 |
| `summary.total_duration` | str | 総実行時間 |
| `features` | dict | Feature名をキーとしたScenarioリストの辞書 |

#### カスタムテンプレート例（テーブル形式）

```jinja2
# テストレポート

生成日時: {{ generation_time }}

## 概要

| 項目 | 値 |
|------|-----|
| 総テスト数 | {{ summary.total_tests }} |
| 成功 | {{ summary.passed }} |
| 失敗 | {{ summary.failed }} |
| 実行時間 | {{ summary.total_duration }} |

## 詳細結果

{% for feature_name, scenarios in features.items() %}
### {{ feature_name }}

{% for scenario in scenarios %}
**{{ scenario.scenario_name }}** - {{ scenario.status }}
{% endfor %}
{% endfor %}
```

### スクリーンショット機能

テスト失敗時のスクリーンショットをレポートに埋め込むことができます。この機能はpytest-playwrightの`--screenshot`オプションと組み合わせて使用します。

```bash
# 失敗時のスクリーンショットをレポートに含める
pytest --markdown-report=test_report.md --markdown-report-screenshots --screenshot=only-on-failure

# Base64エンコードで直接埋め込む（単一ファイルで完結）
pytest --markdown-report=test_report.md --markdown-report-screenshots --markdown-report-embed-images --screenshot=only-on-failure
```

**出力例:**

```markdown
#### Scenario: ログインに失敗する
- **Status**: FAILED
- **Duration**: 0.52s
- **Error**:
```
AssertionError: Expected login to succeed
```

**Screenshot:**
![Test failure screenshot](test-results/test-login-failed/test-failed-1.png)
```

**注意:**
- `--screenshot=only-on-failure`オプションはpytest-playwrightが提供するオプションです
- スクリーンショットは`test-results/`ディレクトリに保存されます
- `--markdown-report-embed-images`を使用すると、スクリーンショットがBase64エンコードされてMarkdownに直接埋め込まれます

## サンプルアプリについて

- **ログインページ** (http://localhost:8000/login.html)
  - ユーザー名: `testuser`
  - パスワード: `password`
  - 正しい認証情報でダッシュボードに遷移

- **ダッシュボード** (http://localhost:8000/dashboard.html)
  - ログイン成功後に表示されるページ

## テストの構造

このサンプルプロジェクトでは、テストを以下の3つのファイルに分けて管理しています：

### 1. Featureファイル（Gherkinシナリオ）

`tests/features/login.feature` - ビジネスレベルのテストシナリオ

```gherkin
Feature: ログイン機能

  Scenario: 正常にログインできる
    Given ログインページを開いている
    When 正しいユーザー情報を入力する
    Then ダッシュボードが表示される
```

### 2. テストファイル（エントリポイント）

`tests/test_login.py` - pytestが認識するテストファイル

#### 推奨: `scenarios()` で全シナリオを自動登録

```python
from pytest_bdd import scenarios

# featureファイル内の全シナリオを自動的にテスト化（最もシンプル）
scenarios("features/login.feature")
```

**メリット:**
- 1行で完結
- 新しいシナリオを追加してもコード変更不要

#### 代替: `@scenario` で個別指定

```python
from pytest_bdd import scenario


@scenario("features/login.feature", "正常にログインできる")
def test_正常にログインできる():
    """ログインシナリオのテスト"""
    pass
```

**使うべき場合:**
- 特定のシナリオだけに pytest フィクスチャを適用したい
- テスト関数名をカスタマイズしたい

**重要:**
- ファイル名は `test_*.py` または `*_test.py` にする（pytestの命名規則）

### 3. ステップ定義（実装）

`tests/steps/login_steps.py` - 各ステップの具体的な実装

```python
from pytest_bdd import given, when, then


@given("ログインページを開いている")
def open_login_page(page):
    page.goto("http://localhost:8000/login.html")


@when("正しいユーザー情報を入力する")
def enter_credentials(page):
    page.fill("#username", "testuser")
    page.fill("#password", "password")
    page.click("#login-button")


@then("ダッシュボードが表示される")
def verify_dashboard(page):
    assert page.url == "http://localhost:8000/dashboard.html"
```

**ポイント:**
- ステップ定義は複数のシナリオで再利用可能
- `page` フィクスチャはpytest-playwrightが自動提供
- ステップは Given/When/Then の順序で定義するのが慣例

## 重要な設定ポイント

### ステップ定義の自動読み込み

`tests/conftest.py` で `pytest_plugins` を使用して、ステップ定義を自動的に読み込むように設定しています：

```python
import pytest

# ステップ定義のみを読み込み
# pytest-bdd-md-report プラグインはインストール後に自動で有効化される
pytest_plugins = ["steps.login_steps"]
```

この設定により：
- `tests/steps/login_steps.py` のステップ定義が全てのテストで利用可能
- `pytest-bdd-md-report` プラグインは pip/uv でインストールされていれば自動的に有効化

新しいステップファイルを追加する場合は、`pytest_plugins` のリストに追加してください。

## LLM 連携を前提とした設計

この構成は、LLM による `.feature` ファイルの自動生成と非常に相性が良い設計になっています：

- Gherkin 文言を固定化（表現の統一）
- Step 定義は再利用前提
- DSL は業務用語寄り（CSS セレクタを DSL に漏らさない）

## 関連ドキュメント

- **[README.md](README.md)** - pytest-bdd-md-report パッケージの説明
- **[QUICKSTART.md](QUICKSTART.md)** - 他プロジェクトへの導入ガイド
- **[PUBLISHING.md](PUBLISHING.md)** - PyPI公開手順
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - プロジェクト構造説明

## パッケージの開発

pytest-bdd-md-report パッケージ自体を開発する場合：

```bash
# 編集可能モードでインストール
uv pip install -e .

# ビルド
uv build

# テスト（サンプルプロジェクトで動作確認）
uv run pytest tests/ --markdown-report=test_report.md
```
