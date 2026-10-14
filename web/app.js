/* Plain, offline-capable catalogue. All paper records come from data/papers.yml. */
(() => {
  'use strict';
  const data = window.OPD_DATA;
  const locales = window.OPD_LOCALES;
  if (!data || !locales) return; // The generated static paper list remains readable.
  const $ = id => document.getElementById(id);
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const publicCode = work => ['available', 'available_experimental'].includes(work.code_status);
  const script = document.querySelector('script[src$="app.js"]');
  const assetBase = new URL('./', script.src);
  const byId = new Map(data.works.map(work => [work.id, work]));
  const params = new URLSearchParams(location.search);
  const pageLang = document.documentElement.lang === 'zh-Hans' ? 'zh' : document.documentElement.lang;
  let lang = Object.hasOwn(locales, params.get('lang')) ? params.get('lang') : pageLang;
  if (!Object.hasOwn(locales, lang)) lang = 'en';
  const state = {q: params.get('q') || '', scope: params.get('scope') || 'all', code: params.get('code') || 'all', access: params.get('access') || 'all', sort: params.get('sort') || 'newest'};
  const selected = new Set((params.get('compare') || '').split(',').filter(id => byId.has(id)).slice(0, 3));
  let toastTimer;
  const t = key => locales[lang][key] || key;
  const link = (url, label) => /^https?:\/\//.test(url || '') ? `<a href="${escape(url)}" target="_blank" rel="noopener noreferrer">${escape(label)} ↗</a>` : '';
  const codeClass = work => publicCode(work) ? 'public' : ['announced_not_available', 'linked_access_unverified'].includes(work.code_status) ? 'pending' : '';
  const badge = work => `<span class="code-badge ${codeClass(work)}" title="${escape(t('codeChecked') + ': ' + work.code_last_checked)}">${escape(t(work.code_status))}</span>`;
  const citationButton = work => work.bibtex ? `<button type="button" data-bib="${escape(work.id)}">${escape(t('copyBib'))}</button>` : '';
  const dl = (key, value) => `<dt>${escape(t(key))}</dt><dd>${escape(value)}</dd>`;

  function sourceDetails(work) {
    return `<p class="source-note">${escape(t('sourceText'))}</p><dl lang="en">${dl('interface', work.interface)}${dl('coverage', work.feedback_coverage || '—')}${dl('access', work.teacher_access)}${dl('semantics', work.probability_semantics)}${dl('version', work.checked_version + ' · ' + work.publication)}${dl('rollout', work.evidence_locations.rollout)}${dl('mismatch', work.evidence_locations.mismatch_interface)}${dl('experiment', work.evidence_locations.experiment)}${dl('checked', work.last_verified)}${dl('codeChecked', work.code_last_checked)}<dt>${escape(t('caveats'))}</dt><dd><ul>${work.caveats.map(item => `<li>${escape(item)}</li>`).join('')}</ul></dd></dl><div class="evidence-links">${link(work.urls.full_text || work.urls.paper || work.urls.article, t('paper'))}${link(work.urls.author_publication, 'Author publication')}${link(work.urls.latest_openreview, 'Latest OpenReview')}${(work.implementation_audit?.evidence || []).map((url, i) => link(url, `Code evidence ${i + 1}`)).join('')}</div>`;
  }

  function pairHTML(work) {
    return `<div class="pairs"><small>${escape(t('pair'))}</small>${work.evaluated_pairs.length ? work.evaluated_pairs.map(pair => `<p>${escape(pair.teacher)} → ${escape(pair.student)}</p>`).join('') : `<p>—</p>`}</div>`;
  }

  function paperHTML(work) {
    const paper = work.urls.paper || work.urls.article;
    return `<article class="paper" id="paper-${escape(work.id)}" data-paper-id="${escape(work.id)}"><div class="paper-meta"><span class="scope-badge">${escape(t(work.classification))}</span><time class="paper-date" datetime="${escape(work.first_public_date)}">${escape(work.first_public_date)}</time>${badge(work)}</div><div class="paper-title-row"><h3><span class="short-name">${escape(work.name)}</span>${link(paper, work.title)}</h3><label class="compare-select"><input type="checkbox" data-compare="${escape(work.id)}" ${selected.has(work.id) ? 'checked' : ''}><span>${escape(t('compare'))}</span></label></div><p class="authors">${escape(work.authors.join(' · '))}</p><p class="summary">${escape(work.summary[lang])}</p>${pairHTML(work)}<div class="paper-actions">${link(paper, work.urls.paper ? t('paper') : t('article'))}${work.urls.code ? link(work.urls.code, t(work.code_status)) : `<span>${escape(t('code'))}: ${escape(t(work.code_status))}</span>`}${link(work.urls.project, t('project'))}${citationButton(work)}</div><details><summary>${escape(t('details'))}</summary><div class="detail-content">${sourceDetails(work)}</div></details></article>`;
  }

  function filtered() {
    const terms = state.q.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const matches = data.works.filter(work => {
      const haystack = [work.name, work.title, work.authors.join(' '), work.interface, work.feedback_coverage, work.probability_semantics, work.teacher_access, ...Object.values(work.summary), ...work.evaluated_pairs.map(p => `${p.teacher} ${p.student}`)].join(' ').toLocaleLowerCase();
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
    query.set('lang', lang);
    for (const [key, value] of Object.entries(state)) if (value && value !== 'all' && !(key === 'sort' && value === 'newest')) query.set(key, value);
    if (selected.size) query.set('compare', [...selected].join(','));
    history.replaceState(null, '', `${location.pathname}?${query}${location.hash}`);
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
    updateSelection();
  }

  function renderInterface() {
    document.documentElement.lang = lang === 'zh' ? 'zh-Hans' : lang;
    document.title = `${t('title')} · ${t('subtitle')}`;
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    $('catalogue').setAttribute('aria-label', t('catalogue'));
    $('language').value = lang;
    $('search').placeholder = t('searchHint');
    $('search').value = state.q;
    const guide = {en:'README.md', ja:'README_ja.md', zh:'README_zh.md', ko:'README_ko.md'}[lang];
    $('guide-link').href = `https://github.com/usk-Kimura/awesome-cross-tokenizer-opd/blob/main/${guide}`;
    setOptions('scope', [['all','all'], ['core','allCore'], ...Object.keys(data.classifications).map(key => [key,key])]);
    setOptions('code', [['all','all'], ['public','publicOnly'], ['available_experimental','available_experimental'], ['not_found','not_found'], ['announced_not_available','announced_not_available'], ['linked_access_unverified','linked_access_unverified']]);
    setOptions('access', [['all','all'], ...['logits','scores','hidden','text','varies'].map(key => [key,key])]);
    setOptions('sort', ['newest','oldest','alphabetical'].map(key => [key,key]));
    const stats = [[data.works.length,'records'], [data.works.filter(w => w.classification.startsWith('core_')).length,'core'], [data.works.filter(publicCode).length,'publicCode'], [data.last_verified,'refreshed']];
    $('stats').innerHTML = stats.map(([value, key]) => `<div class="stat ${key === 'refreshed' ? 'date' : ''}"><strong>${escape(value)}</strong><span>${escape(t(key))}</span></div>`).join('');
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
    $('comparison-content').innerHTML = `<div class="compare-grid" style="--columns:${works.length}">${works.map(work => `<section class="compare-card"><h3>${escape(work.name)}</h3><p>${escape(work.summary[lang])}</p>${badge(work)}${pairHTML(work)}${sourceDetails(work)}<div class="paper-actions">${citationButton(work)}</div></section>`).join('')}</div>`;
    $('comparison').showModal();
  }

  $('search').addEventListener('input', e => { state.q = e.target.value; renderPapers(); });
  for (const key of ['scope','code','access','sort']) $(key).addEventListener('change', e => { state[key] = e.target.value; renderPapers(); });
  $('language').addEventListener('change', e => { lang = e.target.value; renderInterface(); });
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
    const citation = e.target.closest('[data-bib]');
    if (citation) copy(byId.get(citation.dataset.bib).bibtex, 'copied', 'copyFallback');
    const close = e.target.closest('[data-close]');
    if (close) $(close.dataset.close).close();
  });
  renderInterface();
})();
