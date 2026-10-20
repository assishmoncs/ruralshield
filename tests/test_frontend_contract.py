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
    dynamic_ids = {"feedbackStatus", "retryScan", "retryHistory", "retryStats"}
    js = APP_PATH.read_text(encoding="utf-8") + "\n" + AUTH_PATH.read_text(encoding="utf-8")
    selector_ids = set(re.findall(r"\$\(['\"]#([A-Za-z][A-Za-z0-9_-]*)['\"]\)", js))
    missing = selector_ids - available_ids - dynamic_ids
    assert not missing, f"JavaScript references missing element IDs: {sorted(missing)}"


def test_theme_language_history_and_auth_controls_are_wired():
    html = HTML_PATH.read_text(encoding="utf-8")
    app = APP_PATH.read_text(encoding="utf-8")
    auth = AUTH_PATH.read_text(encoding="utf-8")
    assert 'id="themeToggle"' in html and "initTheme();" in app
    assert '<button type="button" class="secondary compact" id="authAction">' in html
    assert 'id="language"' in html and "applyLocale(initialLanguage)" in app
    assert 'id="historyContent"' in html and "request('/history')" in app
    assert 'id="statsContent"' in html and "request('/statistics')" in app
    assert "result.persisted === true" in app
    assert "handleSessionExpired" in app and "function handleSessionExpired()" in auth


def test_url_input_has_matching_form_control_styles():
    html = HTML_PATH.read_text(encoding="utf-8")
    css = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")
    assert '<input id="url" type="url"' in html
    assert 'input[type="url"]' in css

def test_public_metadata_does_not_use_example_domain_placeholders():
    html = HTML_PATH.read_text(encoding="utf-8")
    robots = (ROOT / "frontend" / "robots.txt").read_text(encoding="utf-8")
    sitemap = (ROOT / "frontend" / "sitemap.xml").read_text(encoding="utf-8")
    head = html.split("</head>", 1)[0]
    public_metadata = head + robots + sitemap
    assert "ruralshield.example.com" not in public_metadata
    assert "example.com" not in public_metadata


def test_themes_respect_saved_choice_and_reduced_motion():
    app = APP_PATH.read_text(encoding="utf-8")
    css = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")
    assert "prefers-color-scheme: dark" in app
    assert "localStorage.setItem(THEME_KEY, currentTheme)" in app
    assert 'html[data-theme="dark"]' in css
    assert "prefers-reduced-motion: reduce" in css
