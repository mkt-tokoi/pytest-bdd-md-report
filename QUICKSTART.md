# 他のプロジェクトへの導入ガイド

このガイドでは、`pytest-bdd-md-report` を使って、pytest-bdd + pytest-playwright によるE2Eテストを新規プロジェクトに導入する手順を説明します。

## 前提条件

- Python 3.10 以上
- Node.js（Playwrightブラウザのインストールに必要）

## ステップ1: プロジェクト初期化

```bash
# プロジェクトディレクトリ作成
mkdir my-e2e-tests
cd my-e2e-tests

# uvを使う場合
uv init

# または pip/venv を使う場合
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

## ステップ2: 依存関係のインストール

```bash
# uvの場合
uv add pytest pytest-bdd pytest-playwright pytest-bdd-md-report

# pipの場合
pip install pytest pytest-bdd pytest-playwright pytest-bdd-md-report
```

## ステップ3: Playwrightブラウザのインストール

```bash
playwright install chromium
```

## ステップ4: プロジェクト構造作成

```bash
mkdir -p tests/features tests/steps
```

```
my-e2e-tests/
├── tests/
│   ├── features/        # Gherkinシナリオファイル
│   ├── steps/           # ステップ定義
│   └── conftest.py      # pytest設定
└── pyproject.toml       # プロジェクト設定
```

## ステップ5: サンプルシナリオ作成

### `tests/features/login.feature`

```gherkin
Feature: ログイン機能
  ユーザーとしてシステムにログインしたい

  Scenario: 正常にログインできる
    Given ログインページを開いている
    When 正しいユーザー情報を入力する
    Then ダッシュボードが表示される
```

### `tests/steps/login_steps.py`

```python
import pytest
from pytest_bdd import given, when, then, scenario


@scenario("../features/login.feature", "正常にログインできる")
def test_login():
    """ログインシナリオのテスト"""
    pass


@given("ログインページを開いている")
def open_login_page(page):
    page.goto("https://example.com/login")


@when("正しいユーザー情報を入力する")
def enter_credentials(page):
    page.fill("#username", "testuser")
    page.fill("#password", "password123")
    page.click("#login-button")


@then("ダッシュボードが表示される")
def verify_dashboard(page):
    assert page.is_visible("#dashboard")
```

### `tests/conftest.py`

```python
import pytest

# ステップ定義を自動読み込み
pytest_plugins = ["steps.login_steps"]
```

## ステップ6: pytest設定（オプション）

### `pyproject.toml` または `pytest.ini`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v"
```

## ステップ7: テスト実行

### 基本実行

```bash
pytest
```

### Markdownレポート生成

```bash
# 基本レポート
pytest --markdown-report=test_report.md

# 詳細レポート（ステップ情報を含む）
pytest --markdown-report=test_report.md --markdown-report-verbose

# スクリーンショット付き（失敗時のみ）
pytest --markdown-report=test_report.md \
       --markdown-report-screenshots \
       --screenshot=only-on-failure
```

### CI/CD向けの実行例

```bash
pytest --markdown-report=reports/test_report.md \
       --markdown-report-verbose \
       --markdown-report-screenshots \
       --markdown-report-embed-images \
       --screenshot=only-on-failure \
       --junitxml=reports/junit.xml
```

## カスタムテンプレート（オプション）

### `templates/custom_report.md.j2`

```jinja2
# {{ summary.passed }}/{{ summary.total_tests }} Tests Passed

{% for feature_name, scenarios in features.items() %}
## {{ feature_name }}
{% for scenario in scenarios %}
- {{ scenario.scenario_name }}: {{ scenario.status }}
{% endfor %}
{% endfor %}
```

### 使用方法

```bash
pytest --markdown-report=report.md \
       --markdown-report-template=templates/custom_report.md.j2
```

## GitHub Actions統合例

### `.github/workflows/e2e-tests.yml`

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pytest pytest-bdd pytest-playwright pytest-bdd-md-report
          playwright install chromium

      - name: Run tests
        run: |
          pytest --markdown-report=test_report.md \
                 --markdown-report-verbose \
                 --markdown-report-screenshots \
                 --screenshot=only-on-failure

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-report
          path: |
            test_report.md
            test-results/
```

## トラブルシューティング

### プラグインが認識されない

```bash
# インストール確認
pip list | grep pytest-bdd-md-report

# プラグイン確認
pytest --version
# 出力に "plugins: ... markdown-bdd-report-X.X.X" が含まれるはず
```

### レポートが生成されない

- `--markdown-report=path` オプションを指定していることを確認
- pytest-bdd形式のテストであることを確認（`@scenario` デコレータ使用）

### スクリーンショットが表示されない

- `--screenshot=only-on-failure` オプションを指定していることを確認（pytest-playwrightのオプション）
- `test-results/` ディレクトリが存在することを確認
- テストが実際に失敗していることを確認（成功時はスクリーンショット不要）

## 参考資料

- [pytest-bdd ドキュメント](https://pytest-bdd.readthedocs.io/)
- [pytest-playwright ドキュメント](https://playwright.dev/python/docs/test-runners)
- [Jinja2 テンプレートガイド](https://jinja.palletsprojects.com/)
