# pytest-bdd-md-report

Markdown test report formatter for pytest-bdd with pytest-playwright screenshot support.

## Installation

```bash
pip install pytest-bdd-md-report
```

Or with uv:

```bash
uv add pytest-bdd-md-report
```

### Optional dependencies

```bash
# With pytest-playwright support (for screenshot capture)
pip install pytest-bdd-md-report[playwright]

# With pytest-bdd support
pip install pytest-bdd-md-report[bdd]

# All optional dependencies
pip install pytest-bdd-md-report[all]
```

## Quick Start

```bash
# Generate a markdown report
pytest --markdown-report=test_report.md

# Include detailed step information (Given/When/Then)
pytest --markdown-report=test_report.md --markdown-report-verbose

# Include screenshots for failed tests (requires pytest-playwright)
pytest --markdown-report=test_report.md --markdown-report-screenshots --screenshot=only-on-failure
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--markdown-report=path` | Output path for the Markdown report (required to enable) |
| `--markdown-report-verbose` | Include detailed step information (Given/When/Then) |
| `--markdown-report-template=path` | Custom Jinja2 template file path |
| `--markdown-report-screenshots` | Embed failure screenshots in report |
| `--markdown-report-embed-images` | Base64 encode screenshots directly in markdown |

## Output Example

### Basic Mode

```markdown
## Summary
- **Total Tests**: 3
- **Passed**: 2
- **Failed**: 1

## Test Results

### Feature: Login

#### [PASS] Scenario: Successful login
- **Status**: PASSED
- **Duration**: 1.73s
```

### Verbose Mode (`--markdown-report-verbose`)

```markdown
#### [PASS] Scenario: Successful login
- **Status**: PASSED
- **Duration**: 1.73s

**Steps:**
1. [PASS] **Given** the login page is displayed (0.45s)
2. [PASS] **When** user enters valid credentials (0.98s)
3. [PASS] **Then** dashboard is shown (0.30s)
```

## Custom Templates

Create a custom Jinja2 template to customize the report format.

### Template Variables

| Variable | Type | Description |
|----------|------|-------------|
| `generation_time` | str | Report generation timestamp |
| `summary.total_tests` | int | Total test count |
| `summary.passed` | int | Passed count |
| `summary.failed` | int | Failed count |
| `summary.skipped` | int | Skipped count |
| `summary.total_duration` | str | Total execution time |
| `features` | dict | Feature name to scenario list mapping |

### Example Custom Template

```jinja2
# Test Report

Generated: {{ generation_time }}

| Metric | Value |
|--------|-------|
| Total | {{ summary.total_tests }} |
| Passed | {{ summary.passed }} |
| Failed | {{ summary.failed }} |

{% for feature_name, scenarios in features.items() %}
## {{ feature_name }}

{% for scenario in scenarios %}
- **{{ scenario.scenario_name }}**: {{ scenario.status }}
{% endfor %}
{% endfor %}
```

## Screenshot Support

Capture screenshots for failed tests using pytest-playwright:

```bash
# Screenshots saved as file references
pytest --markdown-report=test_report.md --markdown-report-screenshots --screenshot=only-on-failure

# Screenshots embedded as Base64 (single-file report)
pytest --markdown-report=test_report.md --markdown-report-screenshots --markdown-report-embed-images --screenshot=only-on-failure
```

**Note:** `--screenshot=only-on-failure` is a pytest-playwright option. Screenshots are saved to `test-results/` directory.

## Requirements

- Python >= 3.10
- pytest >= 7.0.0
- jinja2 >= 3.1.0

### Optional

- pytest-bdd >= 6.0.0 (for BDD-style tests)
- pytest-playwright >= 0.4.0 (for screenshot capture)

## License

MIT License
