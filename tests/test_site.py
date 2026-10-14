"""Check citation fidelity, multilingual parity, and the generated public artifact."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import html
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_site import build, bib_entries, LANG_FILES, LANG_CODES, page_url, BASE_URL
from sync_code_tables import synchronize


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.papers = 0
        self.metadata = {}
        self.canonical = []
        self.alternates = {}
        self.structured = ""
        self.in_structured = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for name in ["href", "src"]:
            if name in attrs:
                self.urls.append(attrs[name])
        if tag == "article" and attrs.get("class") == "paper":
            self.papers += 1
        if tag == "meta":
            self.metadata[attrs.get("name") or attrs.get("property")] = attrs.get("content")
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical.append(attrs["href"])
        if tag == "link" and attrs.get("rel") == "alternate":
            self.alternates[attrs.get("hreflang")] = attrs.get("href")
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.in_structured = True

    def handle_data(self, data):
        if self.in_structured:
            self.structured += data

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_structured = False


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name) / "site"
        build(cls.output)
        cls.canonical = yaml.safe_load((ROOT / "data/papers.yml").read_text())
        cls.generated = json.loads((cls.output / "data/papers.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_canonical_evidence_and_dates_are_preserved(self):
        self.assertEqual(len(self.canonical["works"]), len(self.generated["works"]))
        for source, rendered in zip(self.canonical["works"], self.generated["works"]):
            for field, value in source.items():
                self.assertEqual(value, rendered[field], (source["id"], field))

    def test_citations_are_complete_original_entries(self):
        original = bib_entries((ROOT / "references.bib").read_text())
        for work in self.generated["works"]:
            if work["record_kind"] == "paper":
                self.assertIsNotNone(work["bibtex"], work["id"])
            if work["bibtex"]:
                self.assertIn(work["bibtex"], original)

    def test_all_languages_have_all_records_and_valid_local_assets(self):
        for lang in LANG_FILES:
            page = self.output / ("index.html" if lang == "en" else lang + "/index.html")
            content = page.read_text()
            parser = Links()
            parser.feed(content)
            self.assertEqual(parser.papers, len(self.canonical["works"]), lang)
            self.assertNotIn("__INITIAL_LIST__", content)
            for url in parser.urls:
                if not url.startswith(("http:", "https:", "data:", "#")):
                    self.assertTrue((page.parent / url.split("?")[0]).exists(), (lang, url))
            for work in self.generated["works"]:
                self.assertTrue(work["summary"][lang], work["id"])

    def test_readme_code_indexes_match_canonical_data(self):
        synchronize(check=True)
        for filename in LANG_FILES.values():
            content = (ROOT / filename).read_text()
            for work in self.canonical["works"]:
                self.assertIn(work["urls"].get("paper") or work["urls"].get("article"), content)

    def test_search_metadata_and_paper_claims_are_in_static_html(self):
        locales = json.loads((ROOT / "web/locales.json").read_text())
        for lang in LANG_FILES:
            page = self.output / ("index.html" if lang == "en" else lang + "/index.html")
            content = page.read_text()
            parser = Links()
            parser.feed(content)
            self.assertEqual(parser.canonical, [page_url(lang)])
            self.assertEqual(parser.metadata["description"], locales[lang]["seoDescription"])
            self.assertEqual(parser.metadata["og:title"], locales[lang]["seoTitle"])
            self.assertEqual(parser.metadata["og:url"], page_url(lang))
            self.assertEqual(parser.metadata["twitter:image"], BASE_URL + "social-card.png")
            self.assertEqual(parser.alternates, {**{LANG_CODES[key]: page_url(key) for key in LANG_FILES}, "x-default": BASE_URL})
            graph = json.loads(parser.structured)["@graph"]
            collection = next(node for node in graph if node["@type"] == "CollectionPage")
            self.assertEqual(collection["inLanguage"], LANG_CODES[lang])
            listing = next(node for node in graph if node["@type"] == "ItemList")
            self.assertEqual(listing["numberOfItems"], len(self.generated["works"]))
            for entry in listing["itemListElement"]:
                work = next(w for w in self.generated["works"] if entry["url"] == page_url(lang) + "#paper-" + w["id"])
                self.assertEqual(entry["item"]["name"], work["title"])
                self.assertEqual(entry["item"]["description"], work["claim"][lang])
                self.assertEqual(entry["item"]["@type"], "ScholarlyArticle" if work["record_kind"] == "paper" else "CreativeWork")
                self.assertIn(html.escape(work["claim"][lang]), content)
                self.assertIn(f'id="paper-{work["id"]}"', content)
                self.assertIn(html.escape(work["claim_source"]), content)
                for author in work["authors"]:
                    self.assertIn(html.escape(author), content)

    def test_sitemap_has_reciprocal_language_urls_and_real_preview_asset(self):
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}
        urls = ET.parse(self.output / "sitemap.xml").findall("s:url", namespace)
        self.assertEqual({url.findtext("s:loc", namespaces=namespace) for url in urls}, {page_url(lang) for lang in LANG_FILES})
        for url in urls:
            self.assertRegex(url.findtext("s:lastmod", namespaces=namespace), r"^\d{4}-\d{2}-\d{2}$")
            self.assertEqual({link.attrib["hreflang"]: link.attrib["href"] for link in url.findall("x:link", namespace)}, {**{LANG_CODES[key]: page_url(key) for key in LANG_FILES}, "x-default": BASE_URL})
        preview = (self.output / "social-card.png").read_bytes()
        self.assertEqual(preview[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(int.from_bytes(preview[16:20], "big"), 1200)
        self.assertEqual(int.from_bytes(preview[20:24], "big"), 630)


if __name__ == "__main__":
    unittest.main()
