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
let currentReport = null;
let reviewDecisions = {};
function refreshCoverage() {
  const result = reviewedCoverage(currentReport, reviewDecisions);
  $('coverage').textContent = result.coverage === null ? '—' : `${result.coverage}%`;
  $('coverage-count').textContent = result.required_count
    ? `${result.matched_count} of ${result.required_count} included job skills found`
    : 'No included job skills. Review the suggestions below.';
  const total = currentReport.requirements.reduce((n, row) => n + row.candidates.length, 0);
  const accepted = Object.values(reviewDecisions).filter(x => x === 'accepted').length;
  const rejected = Object.values(reviewDecisions).filter(x => x === 'rejected').length;
  $('suggestion-count').textContent = `${accepted} accepted · ${rejected} rejected · ${total - accepted - rejected} awaiting review. Pending and rejected pairs earn no credit. The job requirement total stays fixed.`;
  renderList('matched', result.matched, 'No included skills in common.');
  renderList('missing', result.missing, result.required_count ? 'No gaps among included job skills.' : 'No included job skills to compare.');
  renderList('additional', result.additional, 'No additional included skills.');
  for (const key of ['matched', 'missing', 'additional']) $(`${key}-count`).textContent = `(${result[key].length})`;
}
function renderPairs() {
  const list = $('pair-suggestions'); list.replaceChildren();
  let count = 0;
  for (const row of currentReport.requirements) row.candidates.forEach((candidate, index) => {
    count++;
    const key = JSON.stringify([row.uri, index]);
    const li = document.createElement('li');
    const label = document.createElement('strong'); label.textContent = `Job skill: ${row.skill}`;
    const job = document.createElement('p'); job.textContent = `Job says: “${candidate.job_text}”`;
    const resume = document.createElement('p'); resume.textContent = `Résumé says: “${candidate.resume_text}”`;
    const controls = document.createElement('div'); controls.className = 'review-controls';
    controls.setAttribute('role','group'); controls.setAttribute('aria-label', `Does this résumé evidence satisfy ${row.skill}?`);
    const status = document.createElement('p'); status.className='review-status'; status.setAttribute('aria-live','polite');
    const buttons=[];
    function update() {
      for (const [button,decision] of buttons) button.setAttribute('aria-pressed', String(reviewDecisions[key]===decision));
      status.textContent=reviewDecisions[key]==='accepted' ? 'Accepted by you · this job skill counts as matched'
        :reviewDecisions[key]==='rejected' ? 'Rejected · no credit from this pair' : 'Awaiting decision · no credit yet';
    }
    for(const [decision,title] of [['rejected','✕ Not equivalent'],['accepted','✓ Equivalent']]) {
      const button=document.createElement('button'); button.type='button'; button.textContent=title;
      button.addEventListener('click',()=>{
        if(reviewDecisions[key]===decision) delete reviewDecisions[key]; else reviewDecisions[key]=decision;
        update(); refreshCoverage();
      }); buttons.push([button,decision]); controls.append(button);
    }
    update(); li.append(label,job,resume,controls,status); list.append(li);
  });
  if(!count) renderList('pair-suggestions', [], 'No additional résumé–job pairs were found for review.');
  $('review-count').textContent=`(${count})`;
  const requirements=$('requirements-list'); requirements.replaceChildren();
  for(const row of currentReport.requirements) {
    const li=document.createElement('li'); li.textContent=`${row.skill} — “${row.texts.join('”; “')}”${row.confirmed ? '' : ' (model interpretation)'}`; requirements.append(li);
  }
}
function renderReport(data) {
  currentReport = data; reviewDecisions = {};
  refreshCoverage();
  $('similarity').textContent = `Text similarity: ${data.text_similarity}% · A separate wording comparison.`;
  renderPairs();
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
