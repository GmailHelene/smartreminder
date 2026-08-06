"""
End-to-end tests for SmartReminder Pro using Playwright (real browser).

Unlike the request-based smoke test, this executes JavaScript, so it can catch
broken inline handlers (important for the strict-CSP work) and verify visual
layout (e.g. that the calendar sits above the boards section).

Run:
    pip install -r requirements-dev.txt
    playwright install chromium
    # against the live site (default):
    pytest tests/e2e -q
    # or against a local/staging instance:
    SMARTREMINDER_URL=http://localhost:8080 pytest tests/e2e -q
"""
import os
import re
import secrets
import pytest

BASE_URL = os.environ.get("SMARTREMINDER_URL", "https://smartremind-production.up.railway.app")


def _unique_email():
    return f"pwtest_{secrets.token_hex(4)}@example.com"


@pytest.fixture()
def account(page):
    """Register a throwaway account, yield its creds, and delete it afterwards."""
    email, password = _unique_email(), "PlaywrightPass123"
    page.goto(f"{BASE_URL}/login")
    page.click("button[data-bs-target='#registerModal']")
    reg = page.locator("#registerForm")
    reg.locator("input[name='username']").fill(email)
    page.fill("#reg-password", password)
    page.fill("#reg-password-confirm", password)
    page.check("#reg-consent")
    reg.locator("button[type='submit']").click()
    page.wait_for_url(re.compile(r"/dashboard"), timeout=15000)
    yield {"email": email, "password": password}
    # Cleanup: delete the account if still logged in
    try:
        page.on("dialog", lambda d: d.accept())
        page.goto(f"{BASE_URL}/dashboard")
        page.locator("form[action$='/delete-account'] button[type='submit']").click()
        page.wait_for_url(re.compile(r"/login"), timeout=10000)
    except Exception:
        pass


def test_login_page_loads(page):
    page.goto(f"{BASE_URL}/login")
    assert "SmartReminder" in page.title()
    assert page.locator("#username").is_visible()
    assert page.locator("a[href$='/personvern']").count() >= 1  # GDPR link present


def test_register_and_dashboard(account, page):
    assert page.locator("#dashboardToolbar").is_visible()
    assert "Mine påminnelser" in page.content()


def test_calendar_is_above_boards(account, page):
    """The dashboard must lead with the calendar; boards come later."""
    cal = page.locator("#calendarSection")
    boards = page.locator("#boardsSection")
    cal.scroll_into_view_if_needed()
    cal_box = cal.bounding_box()
    boards_box = boards.bounding_box()
    assert cal_box is not None, "#calendarSection not found"
    assert boards_box is not None, "#boardsSection not found"
    assert cal_box["y"] < boards_box["y"], (
        f"Calendar (y={cal_box['y']}) should be above boards (y={boards_box['y']})"
    )


def test_add_and_complete_reminder(account, page):
    page.click("#newReminderToggle button")
    page.fill("#title", "PW test reminder")
    page.fill("#date", "2026-12-24")
    page.fill("#time", "10:00")
    page.locator("#newReminderCollapse #submit").click()
    page.wait_for_load_state("networkidle")
    assert "PW test reminder" in page.content()


def test_injected_script_is_blocked_by_csp(account, page):
    """XSS defense: a <script> without the nonce must NOT execute (script-src-elem)."""
    page.goto(f"{BASE_URL}/dashboard")
    executed = page.evaluate("""() => new Promise(resolve => {
        window.__xss = false;
        const s = document.createElement('script');
        s.textContent = 'window.__xss = true;';
        document.body.appendChild(s);
        setTimeout(() => resolve(window.__xss === true), 300);
    })""")
    assert executed is False, "Injected inline <script> executed — CSP is NOT blocking it!"


def test_inline_handler_still_works(account, page):
    """Enkel visning toggle uses an onchange handler; it must still fire under the CSP."""
    page.check("#simpleViewSwitch")
    page.wait_for_load_state("networkidle")
    assert "simple-view" in page.content(), "onchange handler did not fire (CSP too strict?)"


def test_no_console_errors_on_dashboard(account, page):
    """Guard for the strict-CSP work: no uncaught JS / CSP errors on the dashboard."""
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_load_state("networkidle")
    critical = [e for e in errors if "Content Security Policy" in e or "Uncaught" in e]
    assert not critical, f"Console errors: {critical}"
