/* Plain, offline-capable catalogue. All paper records come from data/papers.yml. */
(() => {
  'use strict';
  const data = window.OPD_DATA;
  const locales = window.OPD_LOCALES;
  if (!data || !locales) return; // The generated static paper list remains readable.
  const $ = id => document.getElementById(id);
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const publicCode = work => ['available', 'available_experimental'].includes(work.code_status);
  const byId = new Map(data.works.map(work => [work.id, work]));
  const params = new URLSearchParams(location.search);
  const pageLang = document.documentElement.lang === 'zh-Hans' ? 'zh' : document.documentElement.lang;
  let lang = Object.hasOwn(locales, params.get('lang')) ? params.get('lang') : pageLang;
  if (!Object.hasOwn(locales, lang)) lang = 'en';
  const siteBase = new URL('./', document.querySelector('script[src*="site-data.js"]').src);
  const languageURL = language => new URL(language === 'en' ? './' : `${language}/`, siteBase);
  if (lang !== pageLang) {
    const destination = languageURL(lang);
    params.delete('lang');
    destination.search = params.toString();
    destination.hash = location.hash;
    location.replace(destination.href);
    return;
  }
  const state = {q: params.get('q') || '', scope: params.get('scope') || 'all', code: params.get('code') || 'all', access: params.get('access') || 'all', sort: params.get('sort') || 'newest'};
  const selected = new Set((params.get('compare') || '').split(',').filter(id => byId.has(id)).slice(0, 3));
  let toastTimer;
  const t = key => locales[lang][key] || key;
  const link = (url, label) => /^https?:\/\//.test(url || '') ? `<a href="${escape(url)}" target="_blank" rel="noopener noreferrer">${escape(label)} ↗</a>` : '';
  const codeClass = work => publicCode(work) ? 'public' : ['announced_not_available', 'linked_access_unverified'].includes(work.code_status) ? 'pending' : '';
  const badge = work => `<span class="code-badge ${codeClass(work)}" title="${escape(t('codeChecked') + ': ' + work.code_last_checked)}">${escape(t(work.code_status))}</span>`;
  const citationButton = work => work.bibtex ? `<button type="button" data-bib="${escape(work.id)}">${escape(t('copyBib'))}</button>` : '';
  const dl = (key, value, original = false) => `<dt>${escape(t(key))}</dt><dd${original ? ' lang="en"' : ''}>${escape(value)}</dd>`;

  const claimHTML = work => `<div class="paper-claim"><div class="claim-heading"><strong>${escape(t(work.record_kind === 'paper' ? 'claimLabel' : 'resourceClaimLabel'))}</strong>${link(work.claim_source, t('claimSource'))}</div><p class="claim-text">${escape(work.claim[lang])}</p></div>`;

  function implementation(work) {
    const help = {available:'codeAvailableHelp', available_experimental:'codeExperimentalHelp', not_found:'codeMissingHelp', announced_not_available:'codeAnnouncedHelp', linked_access_unverified:'codeLinkedHelp'}[work.code_status];
    return `<div class="implementation"><div class="implementation-row">${badge(work)}${link(work.urls.code, t(work.code_status === 'linked_access_unverified' ? 'codeLink' : 'codeOpen'))}</div>${work.classification === 'paper_claim_implementation_concern' ? `<p class="implementation-concern">${escape(t('codeConcern'))}</p>` : ''}<details class="code-info"><summary>${escape(t('codeHelp'))}</summary><div class="code-explanation"><p>${escape(t(help))}</p><p class="checked-date">${escape(t('codeChecked'))}: <time datetime="${escape(work.code_last_checked)}">${escape(work.code_last_checked)}</time></p></div></details></div>`;
  }

  function sourceDetails(work) {
    const original = `${dl('interface', work.interface, true)}${dl('coverage', work.feedback_coverage || '—', true)}${dl('access', work.teacher_access, true)}${dl('semantics', work.probability_semantics, true)}<dt>${escape(t('caveats'))}</dt><dd lang="en"><ul>${work.caveats.map(item => `<li>${escape(item)}</li>`).join('')}</ul></dd>`;
    const explanation = lang === 'ja' ? `${dl('interface', work.summary.ja)}${dl('coverage', work.japanese.coverage)}${dl('access', work.japanese.access)}${dl('semantics', work.japanese.semantics)}` : original;
    return `<p class="source-note">${escape(t('sourceText'))}</p><dl>${explanation}${dl('version', work.checked_version + ' · ' + work.publication, true)}${dl('rollout', work.evidence_locations.rollout, true)}${dl('mismatch', work.evidence_locations.mismatch_interface, true)}${dl('experiment', work.evidence_locations.experiment, true)}${dl('checked', work.last_verified)}${dl('codeChecked', work.code_last_checked)}</dl>${lang === 'ja' ? `<details class="source-original"><summary>${escape(t('sourceOriginal'))}</summary><dl>${original}</dl></details>` : ''}<div class="evidence-links">${link(work.urls.full_text || work.urls.paper || work.urls.article, t('sourceLink'))}${link(work.urls.author_publication, t('authorPublication'))}${link(work.urls.latest_openreview, t('latestOpenreview'))}${(work.implementation_audit?.evidence || []).map((url, i) => link(url, `${t('codeEvidence')} ${i + 1}`)).join('')}</div>`;
  }

  function pairHTML(work) {
    return `<div class="pairs"><small>${escape(t('pair'))}</small>${work.evaluated_pairs.length ? work.evaluated_pairs.map(pair => `<p lang="en">${escape(pair.teacher)} → ${escape(pair.student)}</p>`).join('') : `<p>${escape(t('noPairs'))}</p>`}</div>`;
  }

  function paperHTML(work) {
    const paper = work.urls.paper || work.urls.article;
    return `<article class="paper" id="paper-${escape(work.id)}" data-paper-id="${escape(work.id)}"><div class="paper-meta"><span class="scope-badge">${escape(t(work.classification))}</span><span class="paper-date">${escape(t('published'))} <time datetime="${escape(work.first_public_date)}">${escape(work.first_public_date)}</time></span></div><div class="paper-title-row"><h3 lang="en">${escape(work.name)}</h3><label class="compare-select"><input type="checkbox" data-compare="${escape(work.id)}" ${selected.has(work.id) ? 'checked' : ''}><span>${escape(t('compare'))}</span></label></div><p class="original-title" lang="en">${link(paper, work.title)}</p>${claimHTML(work)}<p class="authors" lang="en">${escape(work.authors.join(' · '))}</p><div class="method-summary"><span>${escape(t('methodSummary'))}</span><p class="summary">${escape(work.summary[lang])}</p></div>${pairHTML(work)}${implementation(work)}<div class="paper-actions">${link(paper, work.urls.paper ? t('paper') : t('article'))}${link(work.urls.project, t('project'))}${citationButton(work)}</div><details class="method-details"><summary>${escape(t('details'))}</summary><div class="detail-content">${sourceDetails(work)}</div></details></article>`;
  }

  function filtered() {
    const terms = state.q.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const matches = data.works.filter(work => {
      const haystack = [work.name, work.title, work.authors.join(' '), work.interface, work.feedback_coverage, work.probability_semantics, work.teacher_access, ...Object.values(work.summary), ...Object.values(work.claim), ...work.evaluated_pairs.map(p => `${p.teacher} ${p.student}`)].join(' ').toLocaleLowerCase();
      return terms.every(term => haystack.includes(term)) &&
        (state.scope === 'all' || (state.scope === 'core' ? work.classification.startsWith('core_') : work.classification === state.scope)) &&
        (state.code === 'all' || (state.code === 'public' ? publicCode(work) : work.code_status === state.code)) &&
        (state.access === 'all' || work.access_group === state.access);
    });
    return matches.sort((a, b) => state.sort === 'alphabetical' ? a.title.localeCompare(b.title, lang) : (state.sort === 'oldest' ? a.first_public_date.localeCompare(b.first_public_date) : b.first_public_date.localeCompare(a.first_public_date)) || a.title.localeCompare(b.title));
  }

  function setOptions(id, keys) {
    $(id).innerHTML = keys.map(([value, key]) => `<option value="${escape(value)}">${escape(t(key))}</option>`).join('');
    if (!keys.some(([value]) => value === state[id])) state[id] = keys[0][0];
    $(id).value = state[id];
  }

  function updateURL() {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(state)) if (value && value !== 'all' && !(key === 'sort' && value === 'newest')) query.set(key, value);
    if (selected.size) query.set('compare', [...selected].join(','));
    const search = query.toString();
    history.replaceState(null, '', `${location.pathname}${search ? '?' + search : ''}${location.hash}`);
  }

  function updateSelection() {
    $('selection-bar').hidden = !selected.size;
    $('selected-count').textContent = `${selected.size} ${t('selected')}`;
    document.querySelectorAll('[data-compare]').forEach(input => {
      input.checked = selected.has(input.dataset.compare);
      input.disabled = selected.size >= 3 && !input.checked;
    });
    updateURL();
  }

  function renderPapers() {
    const works = filtered();
    $('papers').innerHTML = works.length ? works.map(paperHTML).join('') : `<p class="empty">${escape(t('empty'))}</p>`;
    $('result-count').textContent = `${works.length} ${t('results')}`;
    $('filter-toggle-note').textContent = ['scope','code','access'].some(key => state[key] !== 'all') ? t('filterActive') : '';
    document.querySelectorAll('[data-search]').forEach(button => button.setAttribute('aria-pressed', String(state.q === button.dataset.search)));
    updateSelection();
  }

  function renderInterface() {
    document.documentElement.lang = lang === 'zh' ? 'zh-Hans' : lang;
    document.title = t('seoTitle');
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    $('catalogue').setAttribute('aria-label', t('catalogue'));
    $('language').value = lang;
    $('search').placeholder = t('searchHint');
    $('search').value = state.q;
    $('share').setAttribute('aria-label', t('share'));
    $('share').title = t('share');
    const guide = {en:'README.md', ja:'README_ja.md', zh:'README_zh.md', ko:'README_ko.md'}[lang];
    $('guide-link').href = `https://github.com/usk-Kimura/awesome-cross-tokenizer-opd/blob/main/${guide}`;
    setOptions('scope', [['all','all'], ['core','allCore'], ...Object.keys(data.classifications).map(key => [key,key])]);
    setOptions('code', [['all','all'], ['public','publicOnly'], ['available_experimental','available_experimental'], ['not_found','not_found'], ['announced_not_available','announced_not_available'], ['linked_access_unverified','linked_access_unverified']]);
    setOptions('access', [['all','all'], ...['logits','scores','hidden','text','varies'].map(key => [key,key])]);
    setOptions('sort', ['newest','oldest','alphabetical'].map(key => [key,key]));
    const stats = [[data.works.length,'records'], [data.works.filter(w => w.classification.startsWith('core_')).length,'core'], [data.works.filter(publicCode).length,'publicCode'], [data.last_verified,'refreshed']];
    $('stats').innerHTML = stats.map(([value, key]) => `<div class="stat ${key === 'refreshed' ? 'date' : ''}"${key === 'core' ? ` title="${escape(t('scopeHelp'))}"` : ''}><strong>${escape(value)}</strong><span>${escape(t(key))}</span></div>`).join('');
    renderPapers();
  }

  function notify(message) {
    clearTimeout(toastTimer);
    $('toast').textContent = message;
    $('toast').hidden = false;
    toastTimer = setTimeout(() => { $('toast').hidden = true; }, 3500);
  }

  async function copy(text, success, fallback) {
    try {
      await navigator.clipboard.writeText(text);
      notify(t(success));
    } catch {
      $('copy-heading').textContent = t(fallback);
      $('copy-text').value = text;
      $('copy-dialog').showModal();
      $('copy-text').focus();
      $('copy-text').select();
    }
  }

  function comparison() {
    if (!selected.size) return notify(t('compareEmpty'));
    const works = [...selected].map(id => byId.get(id));
    $('comparison-content').innerHTML = `<div class="compare-grid" style="--columns:${works.length}">${works.map(work => `<section class="compare-card"><h3 lang="en">${escape(work.name)}</h3>${claimHTML(work)}<p>${escape(work.summary[lang])}</p>${implementation(work)}${pairHTML(work)}${sourceDetails(work)}<div class="paper-actions">${citationButton(work)}</div></section>`).join('')}</div>`;
    $('comparison').showModal();
  }

  $('search').addEventListener('input', e => { state.q = e.target.value; renderPapers(); });
  $('filter-toggle').addEventListener('click', () => $('filter-toggle').setAttribute('aria-expanded', String($('filter-toggle').getAttribute('aria-expanded') !== 'true')));
  for (const key of ['scope','code','access','sort']) $(key).addEventListener('change', e => { state[key] = e.target.value; renderPapers(); });
  $('language').addEventListener('change', e => {
    const destination = languageURL(e.target.value);
    destination.search = location.search;
    destination.hash = location.hash;
    location.assign(destination.href);
  });
  $('reset').addEventListener('click', () => { Object.assign(state, {q:'',scope:'all',code:'all',access:'all',sort:'newest'}); renderInterface(); });
  $('clear-selection').addEventListener('click', () => { selected.clear(); updateSelection(); });
  $('open-compare').addEventListener('click', comparison);
  $('share').addEventListener('click', () => copy(location.href, 'linkCopied', 'clipboardFailed'));
  $('download-selected').addEventListener('click', () => {
    const bib = [...selected].map(id => byId.get(id).bibtex).filter(Boolean).join('\n\n') + '\n';
    const url = URL.createObjectURL(new Blob([bib], {type:'application/x-bibtex;charset=utf-8'}));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'selected-papers.bib';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  document.addEventListener('change', e => {
    if (!e.target.matches('[data-compare]')) return;
    const id = e.target.dataset.compare;
    if (e.target.checked) {
      if (selected.size >= 3) { e.target.checked = false; return notify(t('compareLimit')); }
      selected.add(id);
    } else selected.delete(id);
    updateSelection();
  });
  document.addEventListener('click', e => {
    const topic = e.target.closest('[data-search]');
    if (topic) { state.q = topic.dataset.search; $('search').value = state.q; renderPapers(); $('search').focus(); }
    const citation = e.target.closest('[data-bib]');
    if (citation) copy(byId.get(citation.dataset.bib).bibtex, 'copied', 'copyFallback');
    const close = e.target.closest('[data-close]');
    if (close) $(close.dataset.close).close();
  });
  renderInterface();
})();
