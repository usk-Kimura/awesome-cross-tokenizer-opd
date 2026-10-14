"""Keep the four README code indexes synchronized with canonical records."""
from pathlib import Path
import json
import re
import sys
import yaml
from build_site import LANG_FILES, NAMES

ROOT = Path(__file__).resolve().parents[1]
START, END = '<!-- CODE-STATUS:START -->', '<!-- CODE-STATUS:END -->'

def synchronize(check=False):
    data = yaml.safe_load((ROOT / 'data/papers.yml').read_text())
    labels = json.loads((ROOT / 'web/locales.json').read_text())
    changes = []
    for lang, filename in LANG_FILES.items():
        l = labels[lang]
        rows = [START, '<a id="code-availability"></a>', '', '## ' + l['codeHeading'], '', l['codeIntro'], '', '| ' + ' | '.join(l[k] for k in ['tableWork','tableScope','tableCode','tableDate']) + ' |', '|---|---|---|---|']
        for w in data['works']:
            url = w['urls'].get('paper') or w['urls'].get('article')
            code = l[w['code_status']]
            if w['urls'].get('code'):code = '['+code+']('+w['urls']['code']+')'
            rows.append('| [' + NAMES[w['id']] + '](' + url + ') | ' + l[w['classification']] + ' | ' + code + ' | ' + w['code_last_checked'] + ' |')
        rows.extend(['', END])
        block = '\n'.join(rows)
        p = ROOT / filename
        original = p.read_text()
        if START in original:
            updated = re.sub(re.escape(START)+r'.*?'+re.escape(END), lambda _: block, original, flags=re.S)
        else:
            heading = {'en':'## Contributing','ja':'## 更新への協力','zh':'## 贡献与引用','ko':'## 기여와 인용'}[lang]
            if heading not in original:raise ValueError(f'Missing insertion point: {filename}')
            updated = original.replace(heading, block+'\n\n'+heading, 1)
        if updated != original:
            changes.append(filename)
            if not check:p.write_text(updated)
    if check and changes:
        raise SystemExit('Code indexes need regeneration: ' + ', '.join(changes))
    print('Code indexes synchronized: '+', '.join(LANG_FILES.values()))

if __name__=='__main__':synchronize('--check' in sys.argv)
