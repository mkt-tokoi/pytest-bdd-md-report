import pytest

# ステップ定義のみを読み込み
# pytest-markdown-bdd-report プラグインはインストール後に自動で有効化される
pytest_plugins = ["steps.login_steps"]

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 800},
    }


