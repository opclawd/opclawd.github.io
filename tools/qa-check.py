#!/usr/bin/env python3
"""
OpenClaw QA Check - Comprehensive website quality assurance toolkit.

Validates all pages under public/clawdbot/projects/, checks HTML structure,
verifies internal links, validates index.json, and generates a styled report.

Usage:
    python3 tools/qa-check.py              # Basic check
    python3 tools/qa-check.py --verbose    # Detailed output
    python3 tools/qa-check.py --fix        # Auto-fix common issues
    python3 tools/qa-check.py --report     # Generate HTML report
    python3 tools/qa-check.py --fix --report --verbose  # All options

Run from workspace root: /home/node/.openclaw/workspace/
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# ANSI color helpers
# ---------------------------------------------------------------------------
class C:
    """ANSI color codes for terminal output."""
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"

    @staticmethod
    def ok(msg):
        return f"{C.GREEN}PASS{C.RESET} {msg}"

    @staticmethod
    def fail(msg):
        return f"{C.RED}FAIL{C.RESET} {msg}"

    @staticmethod
    def warn(msg):
        return f"{C.YELLOW}WARN{C.RESET} {msg}"

    @staticmethod
    def info(msg):
        return f"{C.CYAN}INFO{C.RESET} {msg}"

    @staticmethod
    def header(msg):
        return f"\n{C.BOLD}{C.WHITE}{'=' * 60}\n  {msg}\n{'=' * 60}{C.RESET}"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "http://clawdbot-web/clawdbot/"
PROJECTS_URL = BASE_URL + "projects/"
PUBLIC_DIR = Path("public/clawdbot")
PROJECTS_DIR = PUBLIC_DIR / "projects"
INDEX_JSON = PROJECTS_DIR / "index.json"
MAIN_INDEX = PUBLIC_DIR / "index.html"
REPORT_FILE = PUBLIC_DIR / "qa-report.html"
HTTP_TIMEOUT = 10


# ---------------------------------------------------------------------------
# HTML structure validator
# ---------------------------------------------------------------------------
class HTMLStructureValidator(HTMLParser):
    """Parses HTML and tracks structural elements."""

    def __init__(self):
        super().__init__()
        self.has_doctype = False
        self.has_html = False
        self.has_head = False
        self.has_body = False
        self.has_title = False
        self.links = []          # href values from <a> tags
        self.asset_refs = []     # src/href for CSS, JS, images
        self.in_title = False
        self.title_text = ""
        self.errors = []
        self._tag_stack = []

    def feed(self, data):
        # Check for doctype before parsing (HTMLParser strips it)
        if re.search(r'<!DOCTYPE\s+html', data, re.IGNORECASE):
            self.has_doctype = True
        super().feed(data)

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        attrs_dict = dict(attrs)
        self._tag_stack.append(tag_lower)

        if tag_lower == "html":
            self.has_html = True
        elif tag_lower == "head":
            self.has_head = True
        elif tag_lower == "body":
            self.has_body = True
        elif tag_lower == "title":
            self.has_title = True
            self.in_title = True

        # Collect links
        if tag_lower == "a" and "href" in attrs_dict:
            href = attrs_dict["href"]
            if href and not href.startswith(("#", "mailto:", "javascript:", "tel:")):
                self.links.append(href)

        # Collect asset references
        if tag_lower == "link" and attrs_dict.get("rel", "").lower() == "stylesheet":
            href = attrs_dict.get("href", "")
            if href:
                self.asset_refs.append(("css", href))
        elif tag_lower == "script" and "src" in attrs_dict:
            self.asset_refs.append(("js", attrs_dict["src"]))
        elif tag_lower == "img" and "src" in attrs_dict:
            self.asset_refs.append(("img", attrs_dict["src"]))

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_text += data


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------
class CheckResult:
    """Stores the result of a single check."""

    def __init__(self, name, category="general"):
        self.name = name
        self.category = category
        self.status = "PASS"       # PASS, FAIL, WARN, FIXED
        self.details = []
        self.sub_checks = []

    def fail(self, msg):
        self.status = "FAIL"
        self.details.append(("FAIL", msg))

    def warn(self, msg):
        if self.status == "PASS":
            self.status = "WARN"
        self.details.append(("WARN", msg))

    def ok(self, msg):
        self.details.append(("PASS", msg))

    def fixed(self, msg):
        self.status = "FIXED"
        self.details.append(("FIXED", msg))

    def info(self, msg):
        self.details.append(("INFO", msg))

    @property
    def passed(self):
        return self.status in ("PASS", "FIXED", "WARN")


class QAReport:
    """Collects all check results."""

    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.end_time = None
        self.fixes_applied = 0

    def add(self, result):
        self.results.append(result)
        return result

    def finalize(self):
        self.end_time = time.time()

    @property
    def elapsed(self):
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def total(self):
        return len(self.results)

    @property
    def passed(self):
        return sum(1 for r in self.results if r.status == "PASS")

    @property
    def failed(self):
        return sum(1 for r in self.results if r.status == "FAIL")

    @property
    def warnings(self):
        return sum(1 for r in self.results if r.status == "WARN")

    @property
    def fixed(self):
        return sum(1 for r in self.results if r.status == "FIXED")

    @property
    def all_passed(self):
        return self.failed == 0


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------
def http_get(url, timeout=HTTP_TIMEOUT):
    """Fetch a URL. Returns (status_code, content_bytes) or (error_code, None)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "OpenClaw-QA/1.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.getcode(), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, None
    except urllib.error.URLError as e:
        return -1, None
    except Exception:
        return -1, None


def url_accessible(url, timeout=HTTP_TIMEOUT):
    """Return True if URL returns HTTP 200."""
    code, _ = http_get(url, timeout)
    return code == 200


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------
def check_main_index(report, verbose=False):
    """Check 6: Main index.html at /clawdbot/."""
    result = report.add(CheckResult("Main index.html", "structure"))

    # File existence
    if not MAIN_INDEX.exists():
        result.fail(f"File not found: {MAIN_INDEX}")
        return result

    content = MAIN_INDEX.read_text(encoding="utf-8", errors="replace")
    if len(content.strip()) == 0:
        result.fail("Main index.html is empty")
        return result

    result.ok(f"File exists ({len(content)} bytes)")

    # HTML structure
    validator = HTMLStructureValidator()
    try:
        validator.feed(content)
    except Exception as e:
        result.warn(f"HTML parse error: {e}")

    _check_html_structure(result, validator, verbose)

    # HTTP check
    code, _ = http_get(BASE_URL)
    if code == 200:
        result.ok(f"HTTP 200 from {BASE_URL}")
    else:
        result.fail(f"HTTP {code} from {BASE_URL}")

    return result


def check_index_json(report, verbose=False, fix=False):
    """Check 2: Validate index.json structure and references."""
    result = report.add(CheckResult("index.json validation", "data"))

    if not INDEX_JSON.exists():
        result.fail(f"File not found: {INDEX_JSON}")
        if fix:
            _fix_create_index_json(result, report)
        return result

    raw = INDEX_JSON.read_text(encoding="utf-8", errors="replace")
    if len(raw.strip()) == 0:
        result.fail("index.json is empty")
        if fix:
            _fix_create_index_json(result, report)
        return result

    # Parse JSON
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        result.fail(f"Invalid JSON: {e}")
        if fix:
            _fix_broken_json(result, raw)
        return result

    if not isinstance(data, list):
        result.fail("index.json root is not an array")
        return result

    result.ok(f"Valid JSON array with {len(data)} entries")

    # Validate each entry
    required_fields = ["name", "file"]
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            result.fail(f"Entry {i} is not an object")
            continue

        for field in required_fields:
            if field not in entry:
                result.warn(f"Entry {i} ({entry.get('name', '?')}): missing '{field}'")

        # Check referenced file exists
        file_ref = entry.get("file", "")
        if file_ref:
            file_path = PROJECTS_DIR / file_ref
            if not file_path.exists():
                result.fail(f"Entry '{entry.get('name', '?')}': file not found: {file_ref}")
            elif file_path.stat().st_size == 0:
                result.fail(f"Entry '{entry.get('name', '?')}': file is empty: {file_ref}")
            elif verbose:
                result.ok(f"Entry '{entry.get('name', '?')}': {file_ref} OK")

    # Check for directories not in index.json
    if PROJECTS_DIR.exists():
        indexed_dirs = set()
        for entry in data:
            f = entry.get("file", "")
            if "/" in f:
                indexed_dirs.add(f.split("/")[0])

        for d in sorted(PROJECTS_DIR.iterdir()):
            if d.is_dir() and d.name not in indexed_dirs:
                result.warn(f"Directory '{d.name}' exists but has no index.json entry")
                if fix:
                    _fix_add_index_entry(result, data, d.name, report)

    return result


def check_project_pages(report, verbose=False, fix=False):
    """Check 1, 3, 4: Validate all project pages."""
    results = []

    if not PROJECTS_DIR.exists():
        r = report.add(CheckResult("Projects directory", "structure"))
        r.fail(f"Directory not found: {PROJECTS_DIR}")
        return results

    # Iterate over test-N directories in sorted order
    test_dirs = sorted(
        [d for d in PROJECTS_DIR.iterdir() if d.is_dir()],
        key=lambda p: _natural_sort_key(p.name)
    )

    for test_dir in test_dirs:
        result = report.add(CheckResult(f"Page: {test_dir.name}", "page"))
        results.append(result)

        index_file = test_dir / "index.html"

        # Check 3: file exists and non-empty
        if not index_file.exists():
            result.fail("index.html does not exist")
            if fix:
                _fix_create_placeholder(result, index_file, test_dir.name, report)
            continue

        content = index_file.read_text(encoding="utf-8", errors="replace")
        if len(content.strip()) == 0:
            result.fail("index.html is empty (0 bytes)")
            if fix:
                _fix_create_placeholder(result, index_file, test_dir.name, report)
            continue

        result.ok(f"File exists ({len(content)} bytes)")

        # Check 4: HTML structure
        validator = HTMLStructureValidator()
        try:
            validator.feed(content)
        except Exception as e:
            result.warn(f"HTML parse error: {e}")
            continue

        _check_html_structure(result, validator, verbose)

        # Check 1: HTTP 200 via internal URL
        page_url = f"{PROJECTS_URL}{test_dir.name}/index.html"
        code, _ = http_get(page_url)
        if code == 200:
            result.ok(f"HTTP 200 OK")
        else:
            result.fail(f"HTTP {code} from {page_url}")

        # Check 5: internal links
        _check_internal_links(result, validator, test_dir, verbose)

        # Check 7: asset references
        _check_assets(result, validator, test_dir, verbose)

    return results


def _check_html_structure(result, validator, verbose):
    """Check 4: Validates HTML has doctype, html, head, body."""
    checks = [
        (validator.has_doctype, "DOCTYPE declaration"),
        (validator.has_html, "<html> tag"),
        (validator.has_head, "<head> tag"),
        (validator.has_body, "<body> tag"),
    ]
    for present, label in checks:
        if present:
            if verbose:
                result.ok(f"Has {label}")
        else:
            result.warn(f"Missing {label}")


def _check_internal_links(result, validator, page_dir, verbose):
    """Check 5: Verify internal links within each page."""
    if not validator.links:
        if verbose:
            result.info("No internal links found")
        return

    checked = 0
    broken = 0
    for href in validator.links:
        # Skip external links
        if href.startswith(("http://", "https://", "//")):
            # Only check links to our own domain
            if "clawdbot-web" not in href and "pulpouplatform.com" not in href:
                continue
            # Check external-but-ours links via HTTP
            if url_accessible(href):
                if verbose:
                    result.ok(f"Link OK: {href}")
            else:
                result.fail(f"Broken link: {href}")
                broken += 1
            checked += 1
            continue

        # Relative link - resolve against page directory
        if href.startswith("/"):
            # Absolute path from site root
            target = PUBLIC_DIR / href.lstrip("/")
        else:
            target = page_dir / href

        # Strip query/fragment
        target_str = str(target).split("?")[0].split("#")[0]
        target = Path(target_str)

        if target.exists() or (target.is_dir() and (target / "index.html").exists()):
            if verbose:
                result.ok(f"Link OK: {href}")
        else:
            result.fail(f"Broken internal link: {href} (resolved to {target})")
            broken += 1
        checked += 1

    if checked > 0 and broken == 0:
        result.ok(f"All {checked} internal links valid")


def _check_assets(result, validator, page_dir, verbose):
    """Check 7: Verify referenced assets (CSS, JS, images) are accessible."""
    if not validator.asset_refs:
        if verbose:
            result.info("No asset references found")
        return

    checked = 0
    broken = 0
    for asset_type, ref in validator.asset_refs:
        # Skip data URIs and external CDNs
        if ref.startswith(("data:", "blob:")):
            continue

        if ref.startswith(("http://", "https://", "//")):
            # External asset - check via HTTP
            url = ref if not ref.startswith("//") else "http:" + ref
            if url_accessible(url):
                if verbose:
                    result.ok(f"Asset OK ({asset_type}): {ref}")
            else:
                # External CDN failures are warnings, not hard failures
                result.warn(f"Unreachable asset ({asset_type}): {ref}")
                broken += 1
            checked += 1
        else:
            # Local asset - check file existence
            if ref.startswith("/"):
                target = PUBLIC_DIR / ref.lstrip("/")
            else:
                target = page_dir / ref

            target_str = str(target).split("?")[0].split("#")[0]
            target = Path(target_str)

            if target.exists():
                if verbose:
                    result.ok(f"Asset OK ({asset_type}): {ref}")
            else:
                result.fail(f"Missing local asset ({asset_type}): {ref}")
                broken += 1
            checked += 1

    if checked > 0 and broken == 0:
        result.ok(f"All {checked} assets verified")


# ---------------------------------------------------------------------------
# Auto-fix functions
# ---------------------------------------------------------------------------
def _fix_create_index_json(result, report):
    """Auto-fix: Create index.json from existing directories."""
    entries = []
    if PROJECTS_DIR.exists():
        for d in sorted(PROJECTS_DIR.iterdir(), key=lambda p: _natural_sort_key(p.name)):
            if d.is_dir():
                num = d.name.replace("test-", "")
                entries.append({
                    "name": f"Test {num}: TBD",
                    "description": "Test pendiente de documentacion",
                    "icon": "fa-question",
                    "status": "PENDING",
                    "file": f"{d.name}/index.html",
                    "tags": ["pending"]
                })

    INDEX_JSON.parent.mkdir(parents=True, exist_ok=True)
    INDEX_JSON.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    result.fixed(f"Created index.json with {len(entries)} entries")
    report.fixes_applied += 1


def _fix_add_index_entry(result, data, dir_name, report):
    """Auto-fix: Add missing directory to index.json."""
    num = dir_name.replace("test-", "")
    entry = {
        "name": f"Test {num}: TBD",
        "description": "Test pendiente de documentacion",
        "icon": "fa-question",
        "status": "PENDING",
        "file": f"{dir_name}/index.html",
        "tags": ["pending"]
    }
    data.append(entry)
    INDEX_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    result.fixed(f"Added '{dir_name}' to index.json")
    report.fixes_applied += 1


def _fix_broken_json(result, raw):
    """Auto-fix: Attempt to repair broken JSON."""
    # Common fixes: trailing commas, missing brackets
    fixed = raw.strip()

    # Remove trailing commas before ] or }
    fixed = re.sub(r',\s*([}\]])', r'\1', fixed)

    # Ensure array wrapper
    if not fixed.startswith("["):
        fixed = "[" + fixed
    if not fixed.endswith("]"):
        fixed = fixed + "]"

    try:
        data = json.loads(fixed)
        INDEX_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
        result.fixed(f"Repaired JSON ({len(data)} entries recovered)")
    except json.JSONDecodeError:
        result.fail("Could not auto-repair JSON")


def _fix_create_placeholder(result, file_path, dir_name, report):
    """Auto-fix: Create a placeholder index.html for an empty test."""
    num = dir_name.replace("test-", "")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test {num} - OpenClaw</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 1rem; }}
        .pending {{ color: #f7931e; font-style: italic; }}
    </style>
</head>
<body>
    <h1>Test {num}</h1>
    <p class="pending">This test page is pending content.</p>
    <p><a href="../">Back to projects</a></p>
</body>
</html>
"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(html, encoding="utf-8")
    result.fixed(f"Created placeholder {file_path}")
    report.fixes_applied += 1


# ---------------------------------------------------------------------------
# HTML report generator
# ---------------------------------------------------------------------------
def generate_html_report(report):
    """Check 9: Generate a styled HTML report page."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    elapsed = f"{report.elapsed:.1f}s"

    # Status badge
    if report.all_passed:
        overall_badge = '<span class="badge pass">ALL PASSED</span>'
    else:
        overall_badge = f'<span class="badge fail">{report.failed} FAILED</span>'

    rows = []
    for r in report.results:
        status_class = r.status.lower()
        details_html = ""
        for level, msg in r.details:
            icon = {"PASS": "checkmark", "FAIL": "cross", "WARN": "warning",
                    "FIXED": "wrench", "INFO": "info"}.get(level, "info")
            icon_char = {"checkmark": "&#10004;", "cross": "&#10008;", "warning": "&#9888;",
                         "wrench": "&#128295;", "info": "&#8505;"}.get(icon, "")
            details_html += f'<div class="detail {level.lower()}">{icon_char} {_html_escape(msg)}</div>\n'

        rows.append(f"""
        <tr class="result-row {status_class}">
            <td class="status-cell"><span class="badge {status_class}">{r.status}</span></td>
            <td class="name-cell">{_html_escape(r.name)}</td>
            <td class="category-cell">{_html_escape(r.category)}</td>
            <td class="details-cell">{details_html}</td>
        </tr>""")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QA Report - OpenClaw</title>
    <style>
        :root {{
            --bg: #0d1117;
            --surface: #161b22;
            --border: #30363d;
            --text: #e6edf3;
            --text-dim: #8b949e;
            --pass: #2ea043;
            --fail: #f85149;
            --warn: #d29922;
            --fixed: #58a6ff;
            --info: #8b949e;
            --accent: #ff6b35;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        h1 {{
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
            color: var(--accent);
        }}
        .subtitle {{ color: var(--text-dim); margin-bottom: 2rem; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .summary-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }}
        .summary-card .number {{
            font-size: 2rem;
            font-weight: 700;
        }}
        .summary-card .label {{ color: var(--text-dim); font-size: 0.85rem; }}
        .summary-card.pass .number {{ color: var(--pass); }}
        .summary-card.fail .number {{ color: var(--fail); }}
        .summary-card.warn .number {{ color: var(--warn); }}
        .summary-card.fixed .number {{ color: var(--fixed); }}
        .summary-card.total .number {{ color: var(--text); }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }}
        th {{
            background: #1c2128;
            padding: 0.75rem 1rem;
            text-align: left;
            font-weight: 600;
            font-size: 0.85rem;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        td {{
            padding: 0.6rem 1rem;
            border-top: 1px solid var(--border);
            vertical-align: top;
        }}
        .badge {{
            display: inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .badge.pass {{ background: rgba(46,160,67,0.2); color: var(--pass); }}
        .badge.fail {{ background: rgba(248,81,73,0.2); color: var(--fail); }}
        .badge.warn {{ background: rgba(210,153,34,0.2); color: var(--warn); }}
        .badge.fixed {{ background: rgba(88,166,255,0.2); color: var(--fixed); }}
        .detail {{ font-size: 0.85rem; padding: 0.15rem 0; }}
        .detail.pass {{ color: var(--pass); }}
        .detail.fail {{ color: var(--fail); }}
        .detail.warn {{ color: var(--warn); }}
        .detail.fixed {{ color: var(--fixed); }}
        .detail.info {{ color: var(--info); }}
        .result-row.fail {{ background: rgba(248,81,73,0.04); }}
        .footer {{
            margin-top: 2rem;
            text-align: center;
            color: var(--text-dim);
            font-size: 0.8rem;
        }}
        .filter-bar {{
            margin-bottom: 1rem;
            display: flex;
            gap: 0.5rem;
        }}
        .filter-btn {{
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 0.3rem 0.8rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.8rem;
        }}
        .filter-btn:hover {{ border-color: var(--accent); }}
        .filter-btn.active {{ border-color: var(--accent); background: rgba(255,107,53,0.15); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>OpenClaw QA Report</h1>
        <p class="subtitle">Generated {now} | Duration: {elapsed} | {overall_badge}</p>

        <div class="summary">
            <div class="summary-card total">
                <div class="number">{report.total}</div>
                <div class="label">Total Checks</div>
            </div>
            <div class="summary-card pass">
                <div class="number">{report.passed}</div>
                <div class="label">Passed</div>
            </div>
            <div class="summary-card fail">
                <div class="number">{report.failed}</div>
                <div class="label">Failed</div>
            </div>
            <div class="summary-card warn">
                <div class="number">{report.warnings}</div>
                <div class="label">Warnings</div>
            </div>
            <div class="summary-card fixed">
                <div class="number">{report.fixed}</div>
                <div class="label">Auto-Fixed</div>
            </div>
        </div>

        <div class="filter-bar">
            <button class="filter-btn active" onclick="filterRows('all')">All</button>
            <button class="filter-btn" onclick="filterRows('fail')">Failures</button>
            <button class="filter-btn" onclick="filterRows('warn')">Warnings</button>
            <button class="filter-btn" onclick="filterRows('pass')">Passed</button>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Status</th>
                    <th>Check</th>
                    <th>Category</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>

        <div class="footer">
            <p>OpenClaw QA Toolkit v1.0 | <a href="projects/" style="color: var(--accent);">View Projects</a></p>
        </div>
    </div>

    <script>
    function filterRows(status) {{
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        event.target.classList.add('active');
        document.querySelectorAll('.result-row').forEach(row => {{
            if (status === 'all') {{
                row.style.display = '';
            }} else {{
                row.style.display = row.classList.contains(status) ? '' : 'none';
            }}
        }});
    }}
    </script>
</body>
</html>
"""
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(html, encoding="utf-8")
    return str(REPORT_FILE)


def _html_escape(text):
    """Simple HTML escaping."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _natural_sort_key(s):
    """Sort strings with embedded numbers naturally (test-2 before test-10)."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="OpenClaw QA Check - Comprehensive website quality assurance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run from workspace root: python3 tools/qa-check.py"
    )
    parser.add_argument("--fix", action="store_true",
                        help="Auto-fix common issues (empty files, missing entries, broken JSON)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed output for every check")
    parser.add_argument("--report", "-r", action="store_true",
                        help="Generate HTML report at public/clawdbot/qa-report.html")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Only show failures and summary")
    args = parser.parse_args()

    report = QAReport()

    print(C.header("OpenClaw QA Check"))
    print(f"  {C.DIM}Workspace: {os.getcwd()}{C.RESET}")
    print(f"  {C.DIM}Base URL:  {BASE_URL}{C.RESET}")
    print(f"  {C.DIM}Options:   fix={args.fix} verbose={args.verbose} report={args.report}{C.RESET}")
    print()

    # ---- Run all checks ----

    # 6. Main index
    print(f"{C.BOLD}[1/4] Checking main index...{C.RESET}")
    r = check_main_index(report, args.verbose)
    if not args.quiet:
        _print_result(r, args.verbose)

    # 2. index.json
    print(f"\n{C.BOLD}[2/4] Validating index.json...{C.RESET}")
    r = check_index_json(report, args.verbose, args.fix)
    if not args.quiet:
        _print_result(r, args.verbose)

    # 1, 3, 4, 5, 7. Project pages
    print(f"\n{C.BOLD}[3/4] Checking project pages...{C.RESET}")
    page_results = check_project_pages(report, args.verbose, args.fix)
    for r in page_results:
        if args.quiet and r.passed:
            continue
        _print_result(r, args.verbose)

    # 9. Generate report
    if args.report:
        print(f"\n{C.BOLD}[4/4] Generating HTML report...{C.RESET}")
        report.finalize()
        path = generate_html_report(report)
        print(f"  {C.ok(f'Report written to {path}')}")
    else:
        report.finalize()
        print(f"\n  {C.DIM}[4/4] Skipping HTML report (use --report to generate){C.RESET}")

    # ---- Summary ----
    print(C.header("Summary"))
    print(f"  Total checks:  {report.total}")
    print(f"  {C.GREEN}Passed:      {report.passed}{C.RESET}")
    print(f"  {C.RED}Failed:      {report.failed}{C.RESET}")
    print(f"  {C.YELLOW}Warnings:    {report.warnings}{C.RESET}")
    if report.fixed > 0:
        print(f"  {C.BLUE}Auto-fixed:  {report.fixed}{C.RESET}")
    if report.fixes_applied > 0:
        print(f"  {C.BLUE}Fix actions:  {report.fixes_applied}{C.RESET}")
    print(f"  Duration:      {report.elapsed:.1f}s")
    print()

    if report.all_passed:
        print(f"  {C.BOLD}{C.GREEN}>>> ALL CHECKS PASSED <<<{C.RESET}")
    else:
        print(f"  {C.BOLD}{C.RED}>>> {report.failed} CHECK(S) FAILED <<<{C.RESET}")
        if not args.fix:
            print(f"  {C.DIM}Tip: Run with --fix to auto-repair common issues{C.RESET}")

    print()

    # 10. Exit code
    return 0 if report.all_passed else 1


def _print_result(result, verbose):
    """Print a single check result to terminal."""
    status_map = {
        "PASS":  C.ok,
        "FAIL":  C.fail,
        "WARN":  C.warn,
        "FIXED": lambda m: f"{C.BLUE}FIXD{C.RESET} {m}",
    }
    printer = status_map.get(result.status, C.info)
    print(f"  {printer(result.name)}")
    if verbose or result.status in ("FAIL", "FIXED"):
        for level, msg in result.details:
            indent = "      "
            color = {
                "PASS": C.GREEN, "FAIL": C.RED, "WARN": C.YELLOW,
                "FIXED": C.BLUE, "INFO": C.DIM
            }.get(level, "")
            print(f"{indent}{color}{level}: {msg}{C.RESET}")


if __name__ == "__main__":
    sys.exit(main())
