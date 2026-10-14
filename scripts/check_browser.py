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
        def switch_language(language):
            page.select_option("#language", language)
            page.wait_for_url(urljoin(base_url, "" if language == "en" else language + "/") + "**")
            page.wait_for_load_state("networkidle")
            expect(page.locator("#language")).to_have_value(language)

        locales = json.loads((ROOT / "web/locales.json").read_text())
        for lang, path in [("en", ""), ("ja", "ja/"), ("zh", "zh/"), ("ko", "ko/")]:
            response = page.goto(urljoin(base_url, path), wait_until="networkidle")
            assert response.status == 200
            expect(page.locator(".paper")).to_have_count(total)
            expect(page.locator("#language")).to_have_value(lang)
            expect(page.locator(".original-title + .paper-claim")).to_have_count(total)
            expect(page.locator(".claim-text")).to_have_count(total)
            assert page.locator(".summary").first.inner_text()
            page.select_option("#code", "public")
            expect(page.locator(".paper")).to_have_count(len(available))
            page.click("#reset")
            page.fill("#search", "Rethinking")
            expect(page.locator(".paper")).to_have_count(1)
            expect(page.locator(".claim-heading strong")).to_have_text(locales[lang]["claimLabel"])
            expect(page.locator(".claim-text")).to_contain_text("16")
            expect(page.locator(".code-badge")).to_have_text(locales[lang]["linked_access_unverified"])
            page.locator(".code-info > summary").click()
            expect(page.locator(".code-explanation")).to_contain_text("HTTP 401")
            expect(page.locator(".code-explanation")).to_contain_text("2026-10-14")
            page.locator(".method-details > summary").click()
            expect(page.locator(".detail-content")).to_be_visible()
            assert "2026-10-14" in page.locator(".detail-content").inner_text()
        switch_language("ja")
        page.fill("#search", "OmniOPD")
        expect(page.locator(".code-badge")).to_have_text("公式コードを確認できず")
        page.locator(".code-info > summary").click()
        expect(page.locator(".code-explanation")).to_contain_text("存在しないと断定するものではありません")
        assert page.locator(".implementation-row > a").count() == 0
        page.fill("#search", "OPRD")
        expect(page.locator(".code-badge")).to_have_text("公式コードあり")
        expect(page.locator(".implementation-concern")).to_be_visible()
        page.click("#reset")
        page.click('[data-search="Qwen"]')
        expect(page.locator("#search")).to_have_value("Qwen")
        assert 0 < page.locator(".paper").count() < total
        assert "qwen" in page.locator(".pairs").first.inner_text().lower()
        expect(page.locator('[data-search="Qwen"]')).to_have_attribute("aria-pressed", "true")
        # Verify Japanese glyphs actually use the bundled font rather than a missing fallback.
        page.evaluate("document.fonts.ready")
        session = context.new_cdp_session(page)
        session.send("DOM.enable")
        session.send("CSS.enable")
        document = session.send("DOM.getDocument")
        node = session.send("DOM.querySelector", {"nodeId": document["root"]["nodeId"], "selector": ".summary"})
        fonts = session.send("CSS.getPlatformFontsForNode", {"nodeId": node["nodeId"]})["fonts"]
        assert any(font["familyName"].startswith("Noto Sans JP") and font["isCustomFont"] and font["glyphCount"] > 0 for font in fonts), fonts
        assert page.locator(".summary").first.evaluate("el => parseFloat(getComputedStyle(el).fontSize)") >= 15
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
        for width in [390, 320]:
            page.set_viewport_size({"width": width, "height": 844})
            for lang in ["en", "ja", "zh", "ko"]:
                switch_language(lang)
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (lang, width)
        page.set_viewport_size({"width": 390, "height": 844})
        switch_language("ja")
        page.goto(urljoin(base_url, "ja/"), wait_until="networkidle")
        expect(page.locator("#code")).to_be_hidden()
        page.click("#filter-toggle")
        expect(page.locator("#code")).to_be_visible()
        page.select_option("#code", "linked_access_unverified")
        expect(page.locator(".paper")).to_have_count(1)
        expect(page.locator("#filter-toggle-note")).to_have_text(locales["ja"]["filterActive"])
        page.click("#reset")
        page.click("#filter-toggle")
        expect(page.locator("#code")).to_be_hidden()
        page.evaluate("window.scrollTo(0,0)")
        page.screenshot(path="/tmp/cross-tokenizer-opd-mobile.png", full_page=False)
        page.locator(".paper").first.scroll_into_view_if_needed()
        page.screenshot(path="/tmp/cross-tokenizer-opd-mobile-card.png", full_page=False)
        page.fill("#search", "Rethinking")
        page.locator(".paper").scroll_into_view_if_needed()
        page.screenshot(path="/tmp/cross-tokenizer-opd-mobile-rethinking.png", full_page=False)
        page.set_viewport_size({"width": 1440, "height": 1080})
        expect(page.locator("#code")).to_be_visible()
        page.click("#reset")
        page.evaluate("window.scrollTo(0,0)")
        page.screenshot(path="/tmp/cross-tokenizer-opd-desktop.png", full_page=False)
        assert not errors, errors
        # Legacy shared links migrate to the canonical language route without losing filters.
        page.goto(urljoin(base_url, "?lang=ja&q=Rethinking&compare=cast,bpm"), wait_until="networkidle")
        expect(page.locator("#language")).to_have_value("ja")
        expect(page.locator(".paper")).to_have_count(1)
        expect(page.locator("#selected-count")).to_contain_text("2")
        assert page.url.startswith(urljoin(base_url, "ja/"))
        assert "lang=" not in page.url
        # Without JavaScript, all records and their sources remain discoverable.
        static_context = browser.new_context(java_script_enabled=False)
        static_page = static_context.new_page()
        static_page.goto(urljoin(base_url, "zh/"))
        expect(static_page.locator(".paper")).to_have_count(total)
        expect(static_page.locator(".original-title + .paper-claim")).to_have_count(total)
        latest = max(data["works"], key=lambda work: work["first_public_date"])
        assert latest["summary"]["zh"] in static_page.locator(".paper").first.inner_text()
        assert latest["claim"]["zh"] in static_page.locator(".paper").first.inner_text()
        browser.close()
    print("PASS: claims below titles in four languages, canonical language navigation and legacy links, code states, font rendering, search, filters, comparison, citations, shared URLs, mobile layouts, and static reading.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", nargs="?", default="http://127.0.0.1:8765/")
    check(parser.parse_args().url)
