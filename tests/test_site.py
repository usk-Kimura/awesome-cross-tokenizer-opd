"""Check citation fidelity, multilingual parity, and the generated public artifact."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from html.parser import HTMLParser

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_site import build, bib_entries, LANG_FILES
from sync_code_tables import synchronize


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.papers = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for name in ["href", "src"]:
            if name in attrs:
                self.urls.append(attrs[name])
        if tag == "article" and attrs.get("class") == "paper":
            self.papers += 1


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


if __name__ == "__main__":
    unittest.main()
