'use strict';
const $ = (id) => document.getElementById(id);
let resumeFile = null;
let jobMode = 'paste';
let busy = false;
const form = $('compare-form');
const zone = $('resume-zone');

function clearResults() { $('results').classList.add('hidden'); }
function clearError() { $('error').classList.add('hidden'); $('error').textContent = ''; }
function showError(message) {
  $('error').textContent = message;
  $('error').classList.remove('hidden');
  $('error').focus();
}
function setMode(mode) {
  if (busy) return;
  jobMode = mode;
  $('job-paste').classList.toggle('hidden', mode !== 'paste');
  $('job-link').classList.toggle('hidden', mode !== 'link');
  $('paste-mode').setAttribute('aria-pressed', String(mode === 'paste'));
  $('link-mode').setAttribute('aria-pressed', String(mode === 'link'));
  $('job-url').disabled = mode !== 'link';
  $('job-text').disabled = mode !== 'paste';
  clearError(); clearResults();
}
function chooseFile(file) {
  if (busy) return;
  clearError(); clearResults();
  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    removeFile();
    return showError('Please upload your résumé as a PDF.');
  }
  if (!file.size || file.size > 5 * 1024 * 1024) {
    removeFile();
    return showError(file.size ? 'Please choose a PDF smaller than 5 MB.' : 'That PDF is empty. Please choose another.');
  }
  resumeFile = file;
  $('resume-name').textContent = file.name;
  $('resume-help').textContent = `${(file.size / 1024).toFixed(0)} KB · Click to replace`;
  $('remove-resume').classList.remove('hidden');
  zone.classList.add('selected');
}
function removeFile() {
  resumeFile = null; $('resume').value = '';
  $('resume-name').textContent = 'Drop your résumé here';
  $('resume-help').textContent = 'or browse files';
  $('remove-resume').classList.add('hidden');
  zone.classList.remove('selected');
  clearResults();
}
$('resume').addEventListener('change', (event) => chooseFile(event.target.files[0]));
$('remove-resume').addEventListener('click', removeFile);
for (const name of ['dragenter', 'dragover']) zone.addEventListener(name, (event) => {
  event.preventDefault(); if (!busy) zone.classList.add('dragging');
});
for (const name of ['dragleave', 'drop']) zone.addEventListener(name, (event) => {
  event.preventDefault(); zone.classList.remove('dragging');
});
zone.addEventListener('drop', (event) => {
  if (event.dataTransfer.files.length !== 1) return showError('Please drop one résumé PDF.');
  chooseFile(event.dataTransfer.files[0]);
});
$('paste-mode').addEventListener('click', () => setMode('paste'));
$('link-mode').addEventListener('click', () => setMode('link'));
for (const id of ['job-text', 'job-url']) $(id).addEventListener('input', () => {clearResults(); clearError();});
$('start-over').addEventListener('click', () => {
  if (busy) return;
  form.reset(); removeFile(); setMode('paste');
  $('resume').focus(); window.scrollTo({top: 0, behavior: 'smooth'});
});
function setBusy(value) {
  busy = value;
  form.setAttribute('aria-busy', String(value));
  for (const input of form.querySelectorAll('input, textarea, button')) input.disabled = value;
  if (!value) {
    $('job-url').disabled = jobMode !== 'link';
    $('job-text').disabled = jobMode !== 'paste';
  }
  $('loading').classList.toggle('hidden', !value);
  $('compare').textContent = value ? 'Comparing…' : 'Compare documents ↗';
}
function renderList(id, items, empty) {
  const list = $(id); list.replaceChildren();
  if (!items.length) {
    const li = document.createElement('li'); li.className = 'empty'; li.textContent = empty; list.append(li); return;
  }
  for (const item of items) {
    const li = document.createElement('li'); li.textContent = item; list.append(li);
  }
}
function renderEvidence(id, items) {
  const list = $(id); list.replaceChildren();
  if (!items.length) return renderList(id, [], 'None detected.');
  for (const item of items) {
    const li = document.createElement('li');
    const label = document.createElement('strong'); label.textContent = item.skill;
    const quote = document.createElement('p'); quote.textContent = `“${item.text}”`;
    li.append(label, quote); list.append(li);
  }
}
function renderReport(data) {
  $('coverage').textContent = data.coverage === null ? '—' : `${data.coverage}%`;
  $('coverage-count').textContent = data.required_count
    ? `${data.matched_count} of ${data.required_count} confirmed job skills found`
    : 'No confirmed job skills found. Review the suggestions below.';
  const reviewCount = data.resume_suggestions.length + data.job_suggestions.length;
  $('suggestion-count').textContent = `${data.job_suggestions.length} job suggestions and ${data.resume_suggestions.length} résumé suggestions excluded from coverage.`;
  $('similarity').textContent = `Text similarity: ${data.text_similarity}% · A separate wording comparison.`;
  renderList('matched', data.matched, 'No confirmed skills in common were found.');
  renderList('missing', data.missing, data.required_count ? 'No gaps among the confirmed job skills.' : 'No confirmed job skills to compare.');
  renderList('additional', data.additional, 'No additional confirmed skills found.');
  for (const key of ['matched', 'missing', 'additional']) $(`${key}-count`).textContent = `(${data[key].length})`;
  $('review-count').textContent = `(${reviewCount})`;
  renderEvidence('resume-suggestions', data.resume_suggestions);
  renderEvidence('job-suggestions', data.job_suggestions);
  renderEvidence('resume-evidence', data.resume_evidence);
  renderEvidence('job-evidence', data.job_evidence);
  $('results').classList.remove('hidden');
  $('results').focus({preventScroll: true});
  $('results').scrollIntoView({behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start'});
}
form.noValidate = true;
form.addEventListener('submit', async (event) => {
  event.preventDefault(); if (busy) return;
  clearError(); clearResults();
  if (!resumeFile) return showError('Add your résumé PDF to continue.');
  const text = $('job-text').value.trim();
  const url = $('job-url').value.trim();
  if (jobMode === 'paste' && !text) return showError('Paste the job description to continue.');
  if (jobMode === 'link') {
    try {
      const parsed = new URL(url);
      if (!['https:', 'http:'].includes(parsed.protocol)) throw new Error();
    } catch { return showError('Enter a complete job link beginning with https:// or http://.'); }
  }
  const payload = new FormData(); payload.append('resume', resumeFile);
  payload.append(jobMode === 'paste' ? 'job_text' : 'job_url', jobMode === 'paste' ? text : url);
  setBusy(true);
  try {
    const response = await fetch('/api/compare', {method: 'POST', body: payload});
    const data = await response.json().catch(() => {throw new Error('The server did not respond as expected. Please try again.');});
    if (!response.ok) throw new Error(data.error || 'The comparison could not finish. Please try again.');
    renderReport(data);
  } catch (error) {
    showError(error instanceof TypeError ? 'Could not reach the server. Check your connection and try again.' : error.message);
  } finally { setBusy(false); }
});
setMode('paste');
