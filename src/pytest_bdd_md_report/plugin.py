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
    group.addoption(
        "--markdown-report-split",
        action="store_true",
        dest="markdown_report_split",
        default=True,
        help="レポートをPASS/FAILごとに分割して出力する（デフォルト: 有効）",
    )
    group.addoption(
        "--no-markdown-report-split",
        action="store_false",
        dest="markdown_report_split",
        help="レポートの分割を無効にする",
    )
    group.addoption(
        "--markdown-report-pass-file",
        action="store",
        dest="markdown_report_pass_file",
        metavar="filename",
        default="report_pass.md",
        help="PASSしたテストのレポートファイル名（デフォルト: report_pass.md）",
    )
    group.addoption(
        "--markdown-report-fail-file",
        action="store",
        dest="markdown_report_fail_file",
        metavar="filename",
        default="report_fail.md",
        help="FAILしたテストのレポートファイル名（デフォルト: report_fail.md）",
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
        split_report=config.option.markdown_report_split,
        pass_file=config.option.markdown_report_pass_file,
        fail_file=config.option.markdown_report_fail_file,
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
        split_report: bool = True,
        pass_file: str = "report_pass.md",
        fail_file: str = "report_fail.md",
    ) -> None:
        """
        Args:
            logfile: 出力先Markdownファイルのパス
            verbose: 詳細なステップ情報（Given/When/Then）を含めるかどうか
            template_path: カスタムテンプレートファイルのパス（Jinja2）
            screenshots: スクリーンショットを埋め込むかどうか
            screenshots_dir: スクリーンショット保存ディレクトリ
            embed_images: Base64エンコードで埋め込むかどうか
            split_report: レポートをPASS/FAILごとに分割するかどうか
            pass_file: PASSしたテストのレポートファイル名
            fail_file: FAILしたテストのレポートファイル名
        """
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.normpath(os.path.abspath(logfile))
        self.verbose = verbose
        self.template_path = template_path
        self.screenshots = screenshots
        self.screenshots_dir = Path(screenshots_dir)
        self.embed_images = embed_images
        self.split_report = split_report
        self.pass_file = pass_file
        self.fail_file = fail_file
        self.test_results: list[dict] = []
        self.start_time: float = 0.0
        # pytest-playwrightのtest-resultsディレクトリ
        self._test_results_dir = Path("test-results")
        # 生成されたレポートファイルのリスト（terminal_summary用）
        self.generated_reports: list[str] = []

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

    def _group_by_feature(self, results: list[dict]) -> dict[str, list[dict]]:
        """テスト結果をFeatureごとにグループ化"""
        features: dict[str, list[dict]] = {}
        for result in results:
            feature_name = result["feature_name"]
            if feature_name not in features:
                features[feature_name] = []
            features[feature_name].append(result)
        return features

    def _render_report(
        self,
        results: list[dict],
        total_duration: float,
        report_title: str | None = None,
    ) -> str:
        """
        テスト結果からMarkdownレポートをレンダリング

        Args:
            results: テスト結果のリスト
            total_duration: テスト全体の実行時間
            report_title: レポートタイトル（テンプレートに渡される）

        Returns:
            レンダリングされたMarkdown文字列
        """
        # サマリー情報を計算
        total_tests = len(results)
        passed = sum(1 for r in results if r["status"] == "PASSED")
        failed = sum(1 for r in results if r["status"] == "FAILED")
        skipped = sum(1 for r in results if r["status"] == "SKIPPED")

        # Featureごとにグループ化
        features = self._group_by_feature(results)

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
                "report_title": report_title,
            }

            try:
                return self._render_with_template(template_path, context)
            except Exception as e:
                print(f"Warning: Failed to render template: {e}")
                print("Falling back to legacy rendering...")
                return self._render_markdown_legacy(total_duration, features)
        else:
            # 従来の方式でMarkdownを生成
            return self._render_markdown_legacy(total_duration, features)

    def _write_report(self, filepath: str, content: str) -> bool:
        """
        レポートをファイルに出力

        Args:
            filepath: 出力先ファイルパス
            content: レポート内容

        Returns:
            出力成功時True、失敗時False
        """
        try:
            output_dir = os.path.dirname(filepath)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Warning: Failed to write markdown report to {filepath}: {e}")
            return False

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

        # メインレポート（全結果）を生成
        main_content = self._render_report(self.test_results, total_duration)
        if self._write_report(self.logfile, main_content):
            self.generated_reports.append(self.logfile)

        # 分割レポートの生成（split_reportがTrueの場合）
        if self.split_report:
            report_dir = os.path.dirname(self.logfile)

            # PASSしたテストのレポート
            passed_results = [r for r in self.test_results if r["status"] == "PASSED"]
            if passed_results:
                pass_filepath = os.path.join(report_dir, self.pass_file) if report_dir else self.pass_file
                pass_filepath = os.path.normpath(os.path.abspath(pass_filepath))
                pass_content = self._render_report(
                    passed_results, total_duration, report_title="Test Report (PASSED)"
                )
                if self._write_report(pass_filepath, pass_content):
                    self.generated_reports.append(pass_filepath)

            # FAILしたテストのレポート（SKIPPEDも含む）
            failed_results = [r for r in self.test_results if r["status"] in ("FAILED", "SKIPPED")]
            if failed_results:
                fail_filepath = os.path.join(report_dir, self.fail_file) if report_dir else self.fail_file
                fail_filepath = os.path.normpath(os.path.abspath(fail_filepath))
                fail_content = self._render_report(
                    failed_results, total_duration, report_title="Test Report (FAILED/SKIPPED)"
                )
                if self._write_report(fail_filepath, fail_content):
                    self.generated_reports.append(fail_filepath)

    def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
        """ターミナルにMarkdownレポートファイルのパスを表示"""
        if len(self.generated_reports) == 1:
            terminalreporter.write_sep("-", f"generated markdown report: {self.generated_reports[0]}")
        elif len(self.generated_reports) > 1:
            terminalreporter.write_sep("-", "generated markdown reports:")
            for report_path in self.generated_reports:
                terminalreporter.write_line(f"  - {report_path}")
