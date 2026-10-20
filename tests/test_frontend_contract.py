"""Static contract tests for the vanilla-JS frontend.

These checks complement syntax validation by catching broken HTML/JavaScript
bindings before deployment; live API behavior still requires an AWS smoke test.
"""
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "frontend" / "index.html"
APP_PATH = ROOT / "frontend" / "app.js"
AUTH_PATH = ROOT / "frontend" / "auth.js"


class MarkupInventory(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.hash_links = []
        self.views = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.append(attributes["id"])
        href = attributes.get("href", "")
        if href.startswith("#"):
            self.hash_links.append(href[1:])
        view = attributes.get("data-view")
        if view:
            self.views.append(view)


def test_frontend_ids_are_unique_and_internal_links_resolve():
    parser = MarkupInventory()
    parser.feed(HTML_PATH.read_text(encoding="utf-8"))
    assert len(parser.ids) == len(set(parser.ids)), "HTML contains duplicate IDs"
    available_ids = set(parser.ids)
    missing_links = set(parser.hash_links) - available_ids
    assert not missing_links, f"Internal links point to missing IDs: {sorted(missing_links)}"


def test_javascript_id_selectors_match_markup_or_documented_dynamic_elements():
    parser = MarkupInventory()
    parser.feed(HTML_PATH.read_text(encoding="utf-8"))
    available_ids = set(parser.ids)
    dynamic_ids = {"feedbackStatus", "retryScan"}
    js = APP_PATH.read_text(encoding="utf-8") + "\n" + AUTH_PATH.read_text(encoding="utf-8")
    selector_ids = set(re.findall(r"\\$\\(['\"]#([A-Za-z][A-Za-z0-9_-]*)['\"]\\)", js))
    missing = selector_ids - available_ids - dynamic_ids
    assert not missing, f"JavaScript references missing element IDs: {sorted(missing)}"


def test_theme_language_history_and_auth_controls_are_wired():
    html = HTML_PATH.read_text(encoding="utf-8")
    app = APP_PATH.read_text(encoding="utf-8")
    auth = AUTH_PATH.read_text(encoding="utf-8")
    assert 'id="themeToggle"' in html and "initTheme();" in app
    assert 'id="language"' in html and "applyLocale(initialLanguage)" in app
    assert 'id="historyContent"' in html and "request('/history')" in app
    assert 'id="statsContent"' in html and "request('/statistics')" in app
    assert "result.persisted === true" in app
    assert "handleSessionExpired" in app and "function handleSessionExpired()" in auth
