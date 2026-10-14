"""Build a portable, static research catalogue from the survey's canonical data."""
from pathlib import Path
import argparse
import html
import hashlib
import json
import re
import shutil

import yaml

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://usk-kimura.github.io/awesome-cross-tokenizer-opd/"
NAMES = {
    "dskdv2": "DSKD / DSKDv2", "simct": "SimCT", "esr": "ESR", "gad": "GAD",
    "ropd": "ROPD", "omniopd": "OmniOPD", "oprd": "OPRD / OPRD-Bridge",
    "btb": "BTB", "reopold": "REOPOLD", "bpm": "BPM", "ovd": "OVD",
    "omnidraft": "OmniDraft", "kdflow": "KDFlow", "easyopd": "EasyOPD", "gold": "GOLD",
    "simpleopd": "SimpleOPD", "compassopd": "CompassOPD", "dvlm": "DVLM",
    "escd": "ESCD", "rethinking": "Rethinking Cross-Tokenizer OPD", "cast": "CAST",
    "mintagent": "Mint-Agent", "actd": "ACTD",
}
ACCESS = {
    "dskdv2": "hidden", "simct": "logits", "esr": "scores", "gad": "text",
    "ropd": "text", "omniopd": "text", "oprd": "hidden", "btb": "scores",
    "reopold": "scores", "bpm": "logits", "ovd": "text", "omnidraft": "logits",
    "kdflow": "varies", "easyopd": "varies", "gold": "logits", "simpleopd": "scores",
    "compassopd": "scores", "dvlm": "hidden", "escd": "logits", "rethinking": "logits",
    "cast": "scores", "mintagent": "scores", "actd": "logits",
}
LANG_FILES = {"en": "README.md", "ja": "README_ja.md", "zh": "README_zh.md", "ko": "README_ko.md"}


def bib_entries(text):
    """Split by balanced braces, preserving complete original citation entries."""
    result = []
    for match in re.finditer(r"@\w+\{", text):
        depth = 1
        end = match.end()
        while depth and end < len(text):
            if text[end] in "{}" and text[end - 1] != "\\":
                depth += 1 if text[end] == "{" else -1
            end += 1
        if depth:
            raise ValueError("Unbalanced BibTeX entry")
        result.append(text[match.start():end])
    return result


def build(output):
    data = yaml.safe_load((ROOT / "data/papers.yml").read_text())
    locales = json.loads((ROOT / "web/locales.json").read_text())
    summaries = json.loads((ROOT / "web/summaries.json").read_text())
    japanese = json.loads((ROOT / "web/japanese-methods.json").read_text())
    citations = bib_entries((ROOT / "references.bib").read_text())
    ids = [work["id"] for work in data["works"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate paper ID")
    if set(japanese) != set(ids):
        raise ValueError("Incomplete Japanese method explanations")
    for lang in LANG_FILES:
        if set(summaries[lang]) != set(ids):
            raise ValueError(f"Incomplete {lang} summaries")
        if set(locales[lang]) != set(locales["en"]):
            raise ValueError(f"Incomplete {lang} interface")
    for work in data["works"]:
        work["name"] = NAMES[work["id"]]
        work["access_group"] = ACCESS[work["id"]]
        urls = [u for u in work["urls"].values() if u]
        work["bibtex"] = next((entry for entry in citations if any(u in entry for u in urls)), None)
        if work["record_kind"] == "paper" and not work["bibtex"]:
            raise ValueError(f"Missing citation: {work['id']}")
        work["summary"] = {lang: summaries[lang][work["id"]] for lang in LANG_FILES}
        work["japanese"] = japanese[work["id"]]
    output.mkdir(parents=True, exist_ok=True)
    for name in ["app.js", "style.css", "locales.json"]:
        shutil.copyfile(ROOT / "web" / name, output / name)
    shutil.copytree(ROOT / "web/fonts", output / "fonts", dirs_exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    interface = json.dumps(locales, ensure_ascii=False).replace("</", "<\\/")
    (output / "site-data.js").write_text(f"window.OPD_DATA = {payload};\nwindow.OPD_LOCALES = {interface};\n")
    revisions = {name: hashlib.sha256((output / name).read_bytes()).hexdigest()[:12] for name in ["style.css", "app.js", "site-data.js"]}
    template = (ROOT / "web/index.html").read_text()
    for lang in LANG_FILES:
        destination = output if lang == "en" else output / lang
        destination.mkdir(exist_ok=True)
        prefix = "./" if lang == "en" else "../"
        initial = []
        for work in sorted(data["works"], key=lambda w: w["first_public_date"], reverse=True):
            url = work["urls"].get("paper") or work["urls"].get("article")
            code = locales[lang][work["code_status"]]
            code_url = work["urls"].get("code")
            code_link = f'<a href="{html.escape(code_url)}">{html.escape(code)}</a>' if code_url else html.escape(code)
            initial.append(f'<article class="paper"><h3 lang="en">{html.escape(work["name"])}</h3><p class="original-title" lang="en"><a href="{html.escape(url)}">{html.escape(work["title"])}</a></p><p class="summary">{html.escape(work["summary"][lang])}</p><div class="implementation"><span class="code-badge">{code_link}</span><p class="checked-date">{html.escape(locales[lang]["codeChecked"])}: {work["code_last_checked"]}</p></div></article>')
        page = template.replace("__LANG__", "zh-Hans" if lang == "zh" else lang)
        page = page.replace("__ASSET_BASE__", prefix).replace("__CANONICAL__", BASE_URL + (lang + "/" if lang != "en" else ""))
        for asset, revision in revisions.items():
            page = page.replace(f'{prefix}{asset}"', f'{prefix}{asset}?v={revision}"')
        page = page.replace("__INITIAL_LIST__", "\n".join(initial))
        page = page.replace(prefix + "README.md", prefix + LANG_FILES[lang])
        for key, value in locales[lang].items():
            page = page.replace("__" + key.upper() + "__", html.escape(value))
        if re.search(r"__[A-Z_]+__", page):
            raise ValueError("Unresolved HTML placeholder")
        (destination / "index.html").write_text(page)
    for name in ["references.bib", "CITATION.cff", "LICENSE", *LANG_FILES.values()]:
        shutil.copyfile(ROOT / name, output / name)
    (output / "data").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "data/papers.yml", output / "data/papers.yml")
    (output / "data/papers.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    (output / ".nojekyll").touch()
    (output / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n")
    locations = [BASE_URL] + [BASE_URL + lang + "/" for lang in LANG_FILES if lang != "en"]
    (output / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{url}</loc></url>" for url in locations) + "</urlset>\n")
    print(f"Built {len(ids)} records in {len(LANG_FILES)} languages: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    build(parser.parse_args().output.resolve())
