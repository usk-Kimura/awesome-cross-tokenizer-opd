"""Optional browser checks. Run against a built-site HTTP URL with Playwright installed."""
import argparse
import json
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def check(base_url):
    data = json.loads((ROOT / "dist/data/papers.json").read_text())
    total = len(data["works"])
    available = [w for w in data["works"] if w["code_status"] in ["available", "available_experimental"]]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(permissions=["clipboard-read", "clipboard-write"])
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        for lang, path in [("en", ""), ("ja", "ja/"), ("zh", "zh/"), ("ko", "ko/")]:
            response = page.goto(urljoin(base_url, path), wait_until="networkidle")
            assert response.status == 200
            expect(page.locator(".paper")).to_have_count(total)
            expect(page.locator("#language")).to_have_value(lang)
            assert page.locator(".summary").first.inner_text()
            page.select_option("#code", "public")
            expect(page.locator(".paper")).to_have_count(len(available))
            page.click("#reset")
            page.fill("#search", "Rethinking")
            expect(page.locator(".paper")).to_have_count(1)
            expect(page.locator(".code-badge")).to_have_count(1)
            page.locator("details").click()
            expect(page.locator(".detail-content")).to_be_visible()
            assert "2026-10-14" in page.locator(".detail-content").inner_text()
        page.click("#reset")
        page.select_option("#access", "text")
        expect(page.locator(".paper")).to_have_count(sum(w["access_group"] == "text" for w in data["works"]))
        page.click("#reset")
        for paper in ["bpm", "rethinking", "cast"]:
            page.locator(f'[data-compare="{paper}"]').check()
        expect(page.locator('[data-compare="simct"]')).to_be_disabled()
        page.click("#open-compare")
        expect(page.locator("#comparison")).to_be_visible()
        expect(page.locator(".compare-card")).to_have_count(3)
        with page.expect_download() as download:
            page.click("#download-selected")
        text = Path(download.value.path()).read_text()
        for arxiv in ["2607.22334", "2610.08448", "2610.13257"]:
            assert arxiv in text
        page.press("#comparison", "Escape")
        page.fill("#search", "Rethinking")
        page.click("[data-bib=rethinking]")
        assert "2610.08448" in page.evaluate("navigator.clipboard.readText()")
        shared_url = page.url
        page.reload(wait_until="networkidle")
        expect(page.locator(".paper")).to_have_count(1)
        expect(page.locator("#selected-count")).to_contain_text("3")
        assert page.url == shared_url
        page.click("#share")
        assert page.evaluate("navigator.clipboard.readText()") == page.url
        page.click("#reset")
        page.fill("#search", "<script>no-such-paper</script>")
        expect(page.locator(".paper")).to_have_count(0)
        expect(page.locator(".empty")).to_be_visible()
        page.click("#reset")
        page.set_viewport_size({"width": 390, "height": 844})
        for lang in ["en", "ja", "zh", "ko"]:
            page.select_option("#language", lang)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), lang
        page.screenshot(path="/tmp/cross-tokenizer-opd-mobile.png", full_page=False)
        assert not errors, errors
        # Without JavaScript, all records and their sources remain discoverable.
        static_context = browser.new_context(java_script_enabled=False)
        static_page = static_context.new_page()
        static_page.goto(urljoin(base_url, "zh/"))
        expect(static_page.locator(".paper")).to_have_count(total)
        latest = max(data["works"], key=lambda work: work["first_public_date"])
        assert latest["summary"]["zh"] in static_page.locator(".paper").first.inner_text()
        browser.close()
    print("PASS: four languages, search, access/code filters, evidence details, comparison, citations, shared URLs, empty state, mobile width, and JavaScript-free reading.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", nargs="?", default="http://127.0.0.1:8765/")
    check(parser.parse_args().url)
