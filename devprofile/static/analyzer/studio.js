/* Form and manual Markdown modes share one sanitized preview. */
(() => {
  const form = document.getElementById('readme-form');
  const source = document.getElementById('readme-source');
  const preview = document.getElementById('preview-box');
  const status = document.getElementById('studio-status');
  const container = document.getElementById('projects-container');
  const draftKey = 'devprofile-studio-v2';
  let manual = !!source.value, timer, draftTimer, controller, generation = 0;
  const setStatus = (message, error = false) => { status.textContent = message; status.classList.toggle('error', error); };
  function render() {
    document.getElementById('word-count').textContent = '· ' + (source.value.trim().match(/\S+/g) || []).length + ' words';
    if (!source.value.trim()) {
      preview.replaceChildren();
      const empty = document.createElement('div'); empty.className = 'preview-empty';
      const title = document.createElement('h3'); title.textContent = 'A good README starts here.';
      const text = document.createElement('p'); text.textContent = 'Enter a name to see your document take shape. You can also open an existing Markdown file.';
      empty.append(title, text); preview.append(empty); return;
    }
    if (!window.marked || !window.DOMPurify) {
      preview.textContent = source.value;
      setStatus('Preview libraries are unavailable. Markdown editing and downloads still work.', true); return;
    }
    preview.innerHTML = DOMPurify.sanitize(marked.parse(source.value, {gfm: true}), {USE_PROFILES: {html: true}, FORBID_TAGS: ['style', 'form', 'input', 'button', 'textarea', 'select', 'iframe'], FORBID_ATTR: ['style']});
    preview.querySelectorAll('a').forEach(a => { a.target = '_blank'; a.rel = 'noopener noreferrer'; });
    preview.querySelectorAll('img').forEach(img => {
      img.loading = 'lazy'; img.referrerPolicy = 'no-referrer';
      img.addEventListener('error', () => { const note = document.createElement('span'); note.className = 'small'; note.textContent = '[' + (img.alt || 'Image') + ' unavailable]'; img.replaceWith(note); }, {once: true});
    });
  }
  function projects() {
    return [...container.querySelectorAll('.project-item')].map(card => Object.fromEntries([...card.querySelectorAll('[data-project-field]')].map(input => [input.dataset.projectField, input.value])));
  }
  function syncProjects() { form.elements.projects_json.value = JSON.stringify(projects()); }
  function addProject(values = {}) {
    if (container.children.length >= 12) { notify('You can add up to 12 projects.'); return; }
    const card = document.createElement('div'); card.className = 'project-item';
    const header = document.createElement('div'); header.className = 'project-header';
    const title = document.createElement('h4'); title.textContent = 'Project';
    const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'button subtle small danger'; remove.textContent = 'Remove';
    remove.addEventListener('click', () => { card.remove(); changed(); document.getElementById('add-project').focus(); });
    header.append(title, remove); card.append(header);
    const grid = document.createElement('div'); grid.className = 'field-grid';
    const uid = crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + String(Math.random());
    for (const [key, label, placeholder] of [['name', 'Project name', 'Your project'], ['description', 'Description', 'What does it do?'], ['tech', 'Technologies', 'Python, Django'], ['url', 'Project URL', 'https://…']]) {
      const field = document.createElement('div'); field.className = 'field full';
      const element = document.createElement('input'); element.type = key === 'url' ? 'url' : 'text'; element.dataset.projectField = key; element.id = uid + '-' + key; element.maxLength = 1000; element.value = typeof values[key] === 'string' ? values[key] : ''; element.placeholder = placeholder;
      const caption = document.createElement('label'); caption.htmlFor = element.id; caption.textContent = label;
      field.append(caption, element); grid.append(field);
    }
    card.append(grid); container.append(card); syncProjects();
  }
  function saveDraft(announce = false) {
    syncProjects();
    const fields = {};
    for (const element of form.elements) {
      if (!element.name || element.name === 'csrfmiddlewaretoken') continue;
      fields[element.name] = element.type === 'checkbox' ? element.checked : element.value;
    }
    try { localStorage.setItem(draftKey, JSON.stringify({fields, projects: projects(), markdown: source.value, manual, saved: new Date().toISOString()})); if (announce) notify('Draft saved in this browser.'); }
    catch (e) { setStatus('Browser storage is unavailable. Download your README to keep it.', true); }
  }
  function scheduleSave() { clearTimeout(draftTimer); draftTimer = setTimeout(() => saveDraft(), 600); }
  function invalidateGeneration() { generation++; clearTimeout(timer); if (controller) controller.abort(); }
  function showErrors(errors = {}) {
    form.querySelectorAll('[data-error-for]').forEach(element => { element.textContent = (errors[element.dataset.errorFor] || []).map(error => error.message).join(' '); });
    for (const element of form.elements) {
      if (element.name) { element.setAttribute('aria-invalid', errors[element.name] ? 'true' : 'false'); }
    }
  }
  async function generate() {
    invalidateGeneration();
    const version = generation;
    syncProjects();
    controller = new AbortController();
    setStatus('Updating preview…');
    try {
      const response = await fetch(form.dataset.previewUrl, {method: 'POST', body: new FormData(form), signal: controller.signal, credentials: 'same-origin'});
      if (version !== generation) return;
      if (!response.headers.get('content-type')?.includes('application/json')) throw new Error('Unexpected response');
      const data = await response.json();
      if (version !== generation) return;
      if (!response.ok) { showErrors(data.errors); setStatus('Check the highlighted fields. Your last preview is preserved.', true); return; }
      showErrors(); manual = false; source.value = data.markdown; render(); saveDraft();
      setStatus('Preview updated. Draft saved in this browser.');
    } catch (error) { if (error.name !== 'AbortError' && version === generation) setStatus('Could not update preview. Your draft is preserved; try Generate from fields again.', true); }
  }
  function changed() {
    updateVisibility();
    invalidateGeneration(); syncProjects(); scheduleSave();
    if (manual) { setStatus('Manual Markdown mode. Generate from fields will replace the current Markdown.'); return; }
    timer = setTimeout(generate, 450);
  }
  document.getElementById('add-project').addEventListener('click', () => { addProject(); changed(); container.lastElementChild.querySelector('input').focus(); });
  form.addEventListener('input', changed);
  form.addEventListener('change', changed);
  form.addEventListener('submit', event => {
    event.preventDefault();
    if (manual && source.value.trim() && !confirm('Replace your manually edited Markdown with a document generated from these fields?')) return;
    generate();
  });
  source.addEventListener('input', () => { invalidateGeneration(); manual = true; render(); scheduleSave(); setStatus('Manual Markdown mode. Changes saved in this browser.'); });
  document.querySelectorAll('[data-editor-tab]').forEach(button => button.addEventListener('click', () => {
    const markdown = button.dataset.editorTab === 'source';
    source.hidden = !markdown; preview.hidden = markdown;
    document.querySelectorAll('[data-editor-tab]').forEach(tab => tab.setAttribute('aria-selected', String(tab === button)));
    if (markdown) source.focus();
  }));
  document.querySelectorAll('[data-mobile]').forEach(button => button.addEventListener('click', () => {
    document.getElementById('studio-layout').dataset.mobileView = button.dataset.mobile;
    document.querySelectorAll('[data-mobile]').forEach(tab => tab.setAttribute('aria-selected', String(tab === button)));
  }));
  document.getElementById('preview-dark').addEventListener('change', event => preview.classList.toggle('preview-dark', event.target.checked));
  document.getElementById('save-draft').addEventListener('click', () => saveDraft(true));
  document.getElementById('restore-draft').addEventListener('click', () => {
    let draft;
    try { draft = JSON.parse(localStorage.getItem(draftKey) || 'null'); } catch (e) {}
    if (!draft?.fields || !Array.isArray(draft.projects)) { notify('No saved draft was found in this browser.'); return; }
    if (!confirm('Restore the saved draft and replace what is currently open?')) return;
    invalidateGeneration();
    for (const [name, value] of Object.entries(draft.fields)) {
      if (name === 'csrfmiddlewaretoken') continue;
      const element = form.elements.namedItem(name);
      if (!element) continue;
      if (element.type === 'checkbox') element.checked = value === true;
      else element.value = typeof value === 'string' ? value : '';
    }
    container.replaceChildren(); draft.projects.slice(0, 12).forEach(addProject); syncProjects();
    source.value = typeof draft.markdown === 'string' ? draft.markdown : ''; manual = !!draft.manual; showErrors(); updateVisibility(); render(); setStatus('Saved draft restored.');
  });
  document.getElementById('clear-draft').addEventListener('click', () => {
    if (!confirm('Delete the browser draft and reset this editor?')) return;
    invalidateGeneration(); clearTimeout(draftTimer);
    try { localStorage.removeItem(draftKey); } catch (e) {}
    location.href = location.pathname;
  });
  document.getElementById('copy-readme').addEventListener('click', async () => {
    if (!source.value.trim()) { notify('Generate or open a README first.'); return; }
    try { await navigator.clipboard.writeText(source.value); notify('Markdown copied.'); }
    catch (e) { source.hidden = false; preview.hidden = true; source.focus(); source.select(); notify('Press Ctrl+C or Cmd+C to copy the selected Markdown.'); }
  });
  document.getElementById('download-readme').addEventListener('click', () => {
    if (!source.value.trim()) { notify('Generate or open a README first.'); return; }
    const url = URL.createObjectURL(new Blob([source.value], {type: 'text/markdown;charset=utf-8'}));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'README.md'; document.body.append(anchor); anchor.click(); anchor.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  document.getElementById('import-markdown').addEventListener('click', () => document.getElementById('markdown-file').click());
  document.getElementById('markdown-file').addEventListener('change', async event => {
    const file = event.target.files[0]; if (!file) return;
    if (file.size > 150000) { notify('Open a Markdown file smaller than 150 KB.'); event.target.value = ''; return; }
    if (source.value.trim() && !confirm('Replace the current Markdown with this file?')) { event.target.value = ''; return; }
    invalidateGeneration();
    const version = generation;
    try {
      const text = await file.text();
      if (version !== generation) return;
      invalidateGeneration(); source.value = text; manual = true; render(); saveDraft(); setStatus('Markdown opened. Edit it in the Markdown tab.');
    } catch (e) { setStatus('Could not read that file.', true); }
    event.target.value = '';
  });
  let initial = [];
  try { initial = JSON.parse(document.getElementById('initial-projects').textContent); } catch (e) {}
  if (Array.isArray(initial)) initial.slice(0, 12).forEach(values => addProject(values || {}));
  function updateVisibility() {
    const isProfile = form.elements.document_type.value === 'profile';
    for (const id of ['details', 'certifications']) {
      const hide = id === 'details' ? isProfile : !isProfile;
      document.getElementById(id).hidden = hide;
      document.getElementById(id).querySelectorAll('input, textarea, select').forEach(element => { element.disabled = hide; });
      const nav = document.querySelector('.studio-nav a[href="#' + id + '"]');
      if (nav) nav.hidden = hide;
    }
    for (const name of ['learning', 'future_goals', 'show_certifications', 'show_stats', 'show_langs', 'show_streak', 'show_graph', 'theme']) {
      form.elements.namedItem(name).closest('.field').hidden = !isProfile;
      form.elements.namedItem(name).disabled = !isProfile;
    }
  }
  updateVisibility(); render();
  if (!source.value && form.elements.name.value) generate();
  else if (!source.value) {
    try { if (localStorage.getItem(draftKey)) setStatus('A saved draft is available. Use Restore draft to continue.'); } catch (e) {}
  }
})();
