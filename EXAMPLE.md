# DSL-Driven E2E Testing with pytest-bdd + pytest-playwright

Python + pytest-bdd + pytest-playwright を使用した DSL 駆動の E2E テストのサンプルプロジェクトです。

## 環境セットアップ

### 1. 仮想環境のアクティベート

```bash
source .venv/bin/activate
# Windows: .venv\Scripts\activate
```

### 2. 依存パッケージのインストール（済み）

```bash
uv add pytest pytest-bdd pytest-playwright
playwright install chromium
```

## プロジェクト構成

```
project-root/
├─ app/
│  ├─ login.html         # サンプルログインページ
│  ├─ dashboard.html     # サンプルダッシュボード
│  └─ server.py          # 開発用 HTTP サーバー
├─ tests/
│  ├─ features/
│  │  └─ login.feature   # Gherkin DSL テストシナリオ
│  ├─ steps/
│  │  └─ login_steps.py  # ステップ定義（Playwright 実装）
│  ├─ plugins/
│  │  ├─ __init__.py
│  │  ├─ markdown_report.py      # Markdownレポートプラグイン
│  │  └─ templates/
│  │     └─ default_report.md.j2 # デフォルトテンプレート
│  ├─ conftest.py        # pytest 設定
│  └─ test_login.py      # pytest エントリポイント
├─ pyproject.toml
└─ README.md
```

## テストの実行方法

### 1. サンプルアプリケーションの起動

別のターミナルでサーバーを起動します：

```bash
source .venv/bin/activate
python app/server.py
```

サーバーは http://localhost:8000/ で起動します。

### 2. テストの実行

#### 通常実行（ヘッドレスモード）

```bash
pytest
```

#### ブラウザを表示して実行

```bash
pytest --headed
```

#### トレース取得（デバッグ用）

```bash
pytest --tracing=on
```

#### 詳細な出力

```bash
pytest -v -s
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

## Gherkin DSL について

`tests/features/login.feature` に以下のような Gherkin 形式でテストシナリオを記述します：

```gherkin
Feature: ログイン機能

  Scenario: 正常にログインできる
    Given ログインページを開いている
    When 正しいユーザー情報を入力する
    Then ダッシュボードが表示される
```

各ステップの実装は `tests/steps/login_steps.py` に記述されています。

## 重要な設定ポイント

### ステップ定義とプラグインの自動読み込み

`tests/conftest.py` で `pytest_plugins` を使用して、ステップ定義とプラグインを自動的に読み込むように設定しています：

```python
pytest_plugins = [
    "steps.login_steps",        # ステップ定義
    "plugins.markdown_report",  # Markdownレポートプラグイン
]
```

この設定により：
- `tests/steps/login_steps.py` のステップ定義が全てのテストで利用可能
- `tests/plugins/markdown_report.py` のMarkdownレポート機能が有効化

新しいステップファイルやプラグインを追加する場合は、`pytest_plugins` のリストに追加してください。

## LLM 連携を前提とした設計

この構成は、LLM による `.feature` ファイルの自動生成と非常に相性が良い設計になっています：

- Gherkin 文言を固定化（表現の統一）
- Step 定義は再利用前提
- DSL は業務用語寄り（CSS セレクタを DSL に漏らさない）

## 参考資料

詳細な導入手順については `DSL-Driven-E2E導入.md` を参照してください。
