/* Shared theme, accessible feedback, and analysis actions. */
window.notify = function(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message; toast.hidden = false;
  clearTimeout(window.toastTimeout);
  window.toastTimeout = setTimeout(() => { toast.hidden = true; }, 3500);
};
const themeToggle = document.getElementById('theme-toggle');
function updateThemeLabel() {
  const next = document.documentElement.dataset.theme === 'dark' ? 'Light' : 'Dark';
  themeToggle.textContent = next + ' theme';
  themeToggle.setAttribute('aria-label', 'Switch to ' + next.toLowerCase() + ' theme');
}
themeToggle.addEventListener('click', () => {
  const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem('devprofile-theme', theme); } catch (e) {}
  updateThemeLabel();
});
updateThemeLabel();
const analysisForm = document.getElementById('analysis-form');
if (analysisForm) {
  analysisForm.addEventListener('submit', () => {
    document.getElementById('analysis-loading').hidden = false;
    analysisForm.querySelector('button[type=submit]').disabled = true;
  });
  window.addEventListener('pageshow', () => {
    document.getElementById('analysis-loading').hidden = true;
    analysisForm.querySelector('button[type=submit]').disabled = false;
  });
  const target = document.getElementById('target');
  target.addEventListener('input', () => {
    const match = target.value.match(/^https:\/\/(github|gitlab)\.com\//i);
    if (match) document.getElementById('provider').value = match[1].toLowerCase();
  });
}
document.querySelectorAll('[data-copy-link]').forEach(button => {
  button.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(location.href); notify('Analysis link copied.'); }
    catch (e) { notify('Copy the link from your browser address bar.'); }
  });
});
document.querySelectorAll('[data-print]').forEach(button => button.addEventListener('click', () => window.print()));
