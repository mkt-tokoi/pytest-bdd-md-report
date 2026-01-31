"""pytest-bdd-md-report: Markdown test report formatter for pytest-bdd."""

from __future__ import annotations

import base64
import os
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

try:
    from jinja2 import Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.reports import TestReport
    from _pytest.terminal import TerminalReporter


def pytest_addoption(parser: Parser) -> None:
    """pytestにMarkdownレポート用のコマンドラインオプションを追加"""
    group = parser.getgroup("markdown-report", "Markdown Report")
    group.addoption(
        "--markdown-report",
        action="store",
        dest="markdown_report_path",
        metavar="path",
        default=None,
        help="Markdownレポートファイルの出力パス（指定しない場合はレポートを生成しない）",
    )
    group.addoption(
        "--markdown-report-verbose",
        action="store_true",
        dest="markdown_report_verbose",
        default=False,
        help="詳細なステップ情報（Given/When/Then）を含める",
    )
    group.addoption(
        "--markdown-report-template",
        action="store",
        dest="markdown_report_template",
        metavar="path",
        default=None,
        help="カスタムMarkdownテンプレートファイルのパス（Jinja2 .j2ファイル）",
    )
    group.addoption(
        "--markdown-report-screenshots",
        action="store_true",
        dest="markdown_report_screenshots",
        default=False,
        help="失敗時のスクリーンショットをレポートに埋め込む",
    )
    group.addoption(
        "--markdown-report-screenshots-dir",
        action="store",
        dest="markdown_report_screenshots_dir",
        metavar="path",
        default="test_screenshots",
        help="スクリーンショットの保存ディレクトリ（デフォルト: test_screenshots）",
    )
    group.addoption(
        "--markdown-report-embed-images",
        action="store_true",
        dest="markdown_report_embed_images",
        default=False,
        help="スクリーンショットをBase64エンコードしてMarkdownに直接埋め込む",
    )


def pytest_configure(config: Config) -> None:
    """pytest設定時にMarkdownレポートプラグインを登録"""
    markdown_path = config.option.markdown_report_path

    # オプションが指定されていない場合はプラグインを登録しない
    if not markdown_path:
        return

    # xdist使用時はワーカーノードでは実行しない
    if hasattr(config, "workerinput"):
        return

    plugin = MarkdownReportPlugin(
        logfile=markdown_path,
        verbose=config.option.markdown_report_verbose,
        template_path=config.option.markdown_report_template,
        screenshots=config.option.markdown_report_screenshots,
        screenshots_dir=config.option.markdown_report_screenshots_dir,
        embed_images=config.option.markdown_report_embed_images,
    )
    config._markdown_report = plugin  # type: ignore[attr-defined]
    config.pluginmanager.register(plugin)


def pytest_unconfigure(config: Config) -> None:
    """pytest終了時にプラグインを登録解除"""
    plugin = getattr(config, "_markdown_report", None)
    if plugin is not None:
        del config._markdown_report  # type: ignore[attr-defined]
        config.pluginmanager.unregister(plugin)


class MarkdownReportPlugin:
    """pytestテストレポートをMarkdown形式で出力するプラグイン"""

    def __init__(
        self,
        logfile: str,
        verbose: bool = False,
        template_path: str | None = None,
        screenshots: bool = False,
        screenshots_dir: str = "test_screenshots",
        embed_images: bool = False,
    ) -> None:
        """
        Args:
            logfile: 出力先Markdownファイルのパス
            verbose: 詳細なステップ情報（Given/When/Then）を含めるかどうか
            template_path: カスタムテンプレートファイルのパス（Jinja2）
            screenshots: スクリーンショットを埋め込むかどうか
            screenshots_dir: スクリーンショット保存ディレクトリ
            embed_images: Base64エンコードで埋め込むかどうか
        """
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.normpath(os.path.abspath(logfile))
        self.verbose = verbose
        self.template_path = template_path
        self.screenshots = screenshots
        self.screenshots_dir = Path(screenshots_dir)
        self.embed_images = embed_images
        self.test_results: list[dict] = []
        self.start_time: float = 0.0
        # pytest-playwrightのtest-resultsディレクトリ
        self._test_results_dir = Path("test-results")

    def _get_default_template_path(self) -> Path:
        """デフォルトテンプレートのパスを取得"""
        return Path(__file__).parent / "templates" / "default_report.md.j2"

    def _find_screenshot_for_test(self, nodeid: str) -> str | None:
        """
        pytest-playwrightが保存したスクリーンショットを検索

        Args:
            nodeid: テストのnodeid（例: tests/test_login.py::test_正常にログインできる）

        Returns:
            スクリーンショットのパス（相対パスまたはBase64 data URL）
        """
        if not self.screenshots:
            return None

        # pytest-playwrightのtest-resultsディレクトリを検索
        if not self._test_results_dir.exists():
            return None

        # nodeidを正規化（pytest-playwrightのディレクトリ命名規則に合わせる）
        # 例: tests/test_login.py::test_正常にログインできる
        #  -> tests-test-login-py-test-... (日本語は別の形式に変換される)

        # nodeidから主要な識別子を抽出
        # パス区切り文字とpytest区切り文字を置換
        normalized = nodeid.replace("/", "-").replace("::", "-").replace(".", "-")

        # 最新の変更時刻を持つディレクトリを探す（複数回テスト実行時の対応）
        latest_screenshot = None
        latest_mtime = 0.0

        # pytest-playwrightは_, /, ., :: をすべて - に変換する
        test_file_part = nodeid.split("::")[0].replace("/", "-").replace(".", "-").replace("_", "-").lower()

        for test_dir in self._test_results_dir.iterdir():
            if not test_dir.is_dir():
                continue

            # ディレクトリ名の先頭部分がマッチするか確認
            # （日本語文字が変換されるため、完全一致ではなく部分一致で検索）
            dir_name = test_dir.name.lower()

            # nodeidの英語部分がディレクトリ名に含まれているか確認
            # 例: "tests-test-login-py-test" がディレクトリ名の先頭にあるか
            if not dir_name.startswith(test_file_part):
                continue

            # スクリーンショットファイルを検索
            screenshots = list(test_dir.glob("*.png"))
            for screenshot in screenshots:
                mtime = screenshot.stat().st_mtime
                if mtime > latest_mtime:
                    latest_mtime = mtime
                    latest_screenshot = screenshot

        if latest_screenshot is None:
            return None

        # Base64埋め込みの場合
        if self.embed_images:
            with open(latest_screenshot, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/png;base64,{image_data}"

        # 相対パスを返す
        report_dir = Path(self.logfile).parent
        try:
            relative_path = latest_screenshot.relative_to(report_dir)
        except ValueError:
            relative_path = latest_screenshot

        return str(relative_path)

    def _render_with_template(self, template_path: Path, context: dict) -> str:
        """Jinja2テンプレートを使用してレンダリング"""
        if not JINJA2_AVAILABLE:
            raise ImportError(
                "Jinja2 is required for template rendering. "
                "Install it with: pip install jinja2"
            )

        with open(template_path, encoding="utf-8") as f:
            template_content = f.read()

        template = Template(template_content)
        return template.render(**context)

    def _render_markdown_legacy(
        self,
        total_duration: float,
        features: dict[str, list[dict]],
    ) -> str:
        """従来の方式でMarkdownを生成（Jinja2未使用時のフォールバック）"""
        total_tests = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "PASSED")
        failed = sum(1 for r in self.test_results if r["status"] == "FAILED")
        skipped = sum(1 for r in self.test_results if r["status"] == "SKIPPED")

        markdown_lines = [
            "# Test Report",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"- **Total Tests**: {total_tests}",
            f"- **Passed**: {passed}",
            f"- **Failed**: {failed}",
            f"- **Skipped**: {skipped}",
            f"- **Total Duration**: {total_duration:.2f}s",
            "",
            "## Test Results",
            "",
        ]

        for feature_name, scenarios in features.items():
            markdown_lines.append(f"### Feature: {feature_name}")
            markdown_lines.append("")

            for scenario in scenarios:
                status_icon = "[PASS]" if scenario["status"] == "PASSED" else "[FAIL]" if scenario["status"] == "FAILED" else "[SKIP]"
                markdown_lines.append(f"#### {status_icon} Scenario: {scenario['scenario_name']}")
                markdown_lines.append(f"- **Status**: {scenario['status']}")
                markdown_lines.append(f"- **Duration**: {scenario['duration']:.2f}s")

                if scenario.get("steps"):
                    markdown_lines.append("")
                    markdown_lines.append("**Steps:**")
                    for i, step in enumerate(scenario["steps"], 1):
                        step_icon = "[PASS]" if step["status"] == "passed" else "[FAIL]"
                        markdown_lines.append(
                            f"{i}. {step_icon} **{step['keyword']}** {step['name']} ({step['duration']:.2f}s)"
                        )
                    markdown_lines.append("")

                if scenario["error_message"]:
                    markdown_lines.append("- **Error**:")
                    markdown_lines.append("```")
                    markdown_lines.append(scenario["error_message"])
                    markdown_lines.append("```")
                    markdown_lines.append("")

                # スクリーンショットを表示
                if scenario.get("screenshot"):
                    markdown_lines.append("**Screenshot:**")
                    markdown_lines.append(f"![Test failure screenshot]({scenario['screenshot']})")
                    markdown_lines.append("")

                markdown_lines.append("---")
                markdown_lines.append("")

        return "\n".join(markdown_lines)

    def pytest_sessionstart(self) -> None:
        """テストセッション開始時に開始時刻を記録"""
        self.start_time = time.time()

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        """
        各テストの実行結果を収集

        Args:
            report: pytestのTestReportオブジェクト
        """
        # pytest-bddテストのみ処理（report.scenario属性の存在確認)
        try:
            scenario = report.scenario
        except AttributeError:
            # pytest-bdd以外のテストはスキップ
            return

        # callフェーズまたはsetup/teardownで失敗した場合のみ処理
        # （setupで失敗した場合もスクリーンショットを取得するため）
        if report.when == "teardown":
            return
        if report.when == "setup" and not report.failed:
            return

        # ステップ情報の収集（verbose モード時のみ）
        steps = []
        if self.verbose and scenario.get("steps"):
            for step in scenario["steps"]:
                steps.append({
                    "keyword": step["keyword"],        # Given/When/Then/And/But
                    "name": step["name"],              # ステップの説明文
                    "status": "failed" if step.get("failed") else "passed",
                    "duration": step.get("duration", 0.0),  # ステップの実行時間（秒）
                })

        # テスト結果を収集（スクリーンショットはpytest_sessionfinishで追加）
        result = {
            "feature_name": scenario["feature"]["name"],
            "scenario_name": scenario["name"],
            "status": "PASSED" if report.passed else "FAILED" if report.failed else "SKIPPED",
            "duration": report.duration,
            "error_message": str(report.longrepr) if report.failed else None,
            "steps": steps,
            "screenshot": None,
            "nodeid": report.nodeid,  # スクリーンショット検索用に保存
        }
        self.test_results.append(result)

    def pytest_sessionfinish(self) -> None:
        """テストセッション終了時にMarkdownレポートを生成・出力"""
        total_duration = time.time() - self.start_time

        # スクリーンショットを検索して追加（pytest-playwrightが保存したもの）
        if self.screenshots:
            for result in self.test_results:
                if result["status"] == "FAILED" and result.get("nodeid"):
                    screenshot_path = self._find_screenshot_for_test(result["nodeid"])
                    if screenshot_path:
                        result["screenshot"] = screenshot_path

        # サマリー情報を計算
        total_tests = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "PASSED")
        failed = sum(1 for r in self.test_results if r["status"] == "FAILED")
        skipped = sum(1 for r in self.test_results if r["status"] == "SKIPPED")

        # Featureごとにグループ化
        features: dict[str, list[dict]] = {}
        for result in self.test_results:
            feature_name = result["feature_name"]
            if feature_name not in features:
                features[feature_name] = []
            features[feature_name].append(result)

        # テンプレート使用の判定
        use_template = JINJA2_AVAILABLE and (
            self.template_path or self._get_default_template_path().exists()
        )

        if use_template:
            # Jinja2テンプレートを使用してレンダリング
            template_path = (
                Path(self.template_path) if self.template_path
                else self._get_default_template_path()
            )

            context = {
                "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed,
                    "failed": failed,
                    "skipped": skipped,
                    "total_duration": f"{total_duration:.2f}s",
                },
                "features": features,
            }

            try:
                markdown_content = self._render_with_template(template_path, context)
            except Exception as e:
                print(f"Warning: Failed to render template: {e}")
                print("Falling back to legacy rendering...")
                markdown_content = self._render_markdown_legacy(total_duration, features)
        else:
            # 従来の方式でMarkdownを生成
            markdown_content = self._render_markdown_legacy(total_duration, features)

        # ファイルに出力（親ディレクトリが存在しない場合は自動作成）
        try:
            output_dir = os.path.dirname(self.logfile)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(self.logfile, "w", encoding="utf-8") as f:
                f.write(markdown_content)
        except Exception as e:
            print(f"Warning: Failed to write markdown report: {e}")

    def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
        """ターミナルにMarkdownレポートファイルのパスを表示"""
        terminalreporter.write_sep("-", f"generated markdown report: {self.logfile}")
