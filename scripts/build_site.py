"""Build a portable, static research catalogue from the survey's canonical data."""
from pathlib import Path
import argparse
import html
import hashlib
import json
import re
import shutil
import subprocess

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
LANG_CODES = {"en": "en", "ja": "ja", "zh": "zh-Hans", "ko": "ko"}
OG_LOCALES = {"en": "en_US", "ja": "ja_JP", "zh": "zh_CN", "ko": "ko_KR"}


def page_url(lang):
    return BASE_URL + (lang + "/" if lang != "en" else "")


def structured_data(data, lang, locale, modified):
    """Describe the catalogue and its external papers without claiming authorship."""
    url = page_url(lang)
    items = []
    for position, work in enumerate(sorted(data["works"], key=lambda w: w["first_public_date"], reverse=True), 1):
        source = work["urls"].get("paper") or work["urls"].get("article")
        item = {
            "@type": "ScholarlyArticle" if work["record_kind"] == "paper" else "CreativeWork",
            "@id": source, "url": source, "name": work["title"],
            "description": work["claim"][lang],
            "author": [{"@type": "Person", "name": name} for name in work["authors"]],
            "datePublished": work["first_public_date"],
        }
        items.append({"@type": "ListItem", "position": position, "url": url + "#paper-" + work["id"], "item": item})
    return {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "@id": BASE_URL + "#website", "url": BASE_URL,
         "name": "Cross-Tokenizer OPD", "inLanguage": list(LANG_CODES.values())},
        {"@type": "CollectionPage", "@id": url, "url": url, "name": locale["seoTitle"],
         "description": locale["seoDescription"], "inLanguage": LANG_CODES[lang],
         "dateModified": modified, "isPartOf": {"@id": BASE_URL + "#website"},
         "mainEntity": {"@id": url + "#research-list"}},
        {"@type": "ItemList", "@id": url + "#research-list", "name": locale["catalogue"],
         "numberOfItems": len(items), "itemListElement": items},
    ]}


def static_paper(work, locale, lang):
    """Keep the primary research content readable before JavaScript runs."""
    e = html.escape
    url = work["urls"].get("paper") or work["urls"].get("article")
    claim_label = locale["claimLabel" if work["record_kind"] == "paper" else "resourceClaimLabel"]
    code = e(locale[work["code_status"]])
    code_url = work["urls"].get("code")
    code_link = f'<a href="{e(code_url)}">{code}</a>' if code_url else code
    pairs = "".join(f'<p lang="en">{e(pair["teacher"])} → {e(pair["student"])}</p>' for pair in work["evaluated_pairs"]) or f'<p>{e(locale["noPairs"])}</p>'
    return f'''<article class="paper" id="paper-{e(work['id'])}" data-paper-id="{e(work['id'])}">
      <div class="paper-meta"><span class="scope-badge">{e(locale[work['classification']])}</span><span class="paper-date">{e(locale['published'])} <time datetime="{work['first_public_date']}">{work['first_public_date']}</time></span></div>
      <h3 lang="en">{e(work['name'])}</h3>
      <p class="original-title" lang="en"><a href="{e(url)}">{e(work['title'])}</a></p>
      <div class="paper-claim"><div class="claim-heading"><strong>{e(claim_label)}</strong><a href="{e(work['claim_source'])}">{e(locale['claimSource'])} ↗</a></div><p class="claim-text">{e(work['claim'][lang])}</p></div>
      <p class="authors" lang="en">{e(' · '.join(work['authors']))}</p>
      <div class="method-summary"><span>{e(locale['methodSummary'])}</span><p class="summary">{e(work['summary'][lang])}</p></div>
      <div class="pairs"><small>{e(locale['pair'])}</small>{pairs}</div>
      <div class="implementation"><span class="code-badge">{code_link}</span><p class="checked-date">{e(locale['codeChecked'])}: {work['code_last_checked']}</p></div>
    </article>'''


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
    claims = json.loads((ROOT / "web/claims.json").read_text())
    japanese = json.loads((ROOT / "web/japanese-methods.json").read_text())
    citations = bib_entries((ROOT / "references.bib").read_text())
    ids = [work["id"] for work in data["works"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate paper ID")
    if set(japanese) != set(ids):
        raise ValueError("Incomplete Japanese method explanations")
    for lang in LANG_FILES:
        if set(claims[lang]) != set(ids) or not all(claims[lang].values()):
            raise ValueError(f"Incomplete {lang} paper claims")
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
        work["claim"] = {lang: claims[lang][work["id"]] for lang in LANG_FILES}
        work["claim_source"] = work["urls"].get("documentation") or work["urls"].get("author_publication") or work["urls"].get("paper") or work["urls"].get("article")
        work["japanese"] = japanese[work["id"]]
    try:
        modified = subprocess.check_output(["git", "log", "-1", "--format=%cs", "--", "web", "data/papers.yml", "references.bib", "scripts/build_site.py"], cwd=ROOT, text=True).strip() or data["last_verified"]
    except (OSError, subprocess.CalledProcessError):
        modified = data["last_verified"]
    output.mkdir(parents=True, exist_ok=True)
    for name in ["app.js", "style.css", "locales.json", "social-card.png"]:
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
        initial = [static_paper(work, locales[lang], lang) for work in sorted(data["works"], key=lambda w: w["first_public_date"], reverse=True)]
        page = template.replace("__LANG__", "zh-Hans" if lang == "zh" else lang)
        page = page.replace("__ASSET_BASE__", prefix).replace("__CANONICAL__", page_url(lang))
        page = page.replace("__OG_LOCALE__", OG_LOCALES[lang])
        page = page.replace("__OG_ALTERNATES__", "\n".join(f'<meta property="og:locale:alternate" content="{code}">' for other, code in OG_LOCALES.items() if other != lang))
        page = page.replace("__STRUCTURED_DATA__", json.dumps(structured_data(data, lang, locales[lang], modified), ensure_ascii=False).replace("<", "\\u003c"))
        page = page.replace(f'<option value="{lang}">', f'<option value="{lang}" selected>')
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
    locations = [page_url(lang) for lang in LANG_FILES]
    alternates = "".join(f'<xhtml:link rel="alternate" hreflang="{LANG_CODES[lang]}" href="{page_url(lang)}"/>' for lang in LANG_FILES) + f'<xhtml:link rel="alternate" hreflang="x-default" href="{BASE_URL}"/>'
    (output / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">' + "".join(f"<url><loc>{url}</loc><lastmod>{modified}</lastmod>{alternates}</url>" for url in locations) + "</urlset>\n")
    print(f"Built {len(ids)} records in {len(LANG_FILES)} languages: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    build(parser.parse_args().output.resolve())
