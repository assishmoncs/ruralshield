const config = window.RURALSHIELD_CONFIG || {};
const API = (config.apiUrl || window.RURALSHIELD_API_URL || localStorage.getItem('ruralshield_api') || '').replace(/\/$/, '');
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const THEME_KEY = 'ruralshield_theme';
const LANGUAGE_KEY = 'ruralshield_language';

function applyTheme(theme, persist = false) {
  const currentTheme = theme === 'dark' ? 'dark' : 'light';
  document.documentElement.dataset.theme = currentTheme;
  const metaTheme = $('meta[name="theme-color"]');
  if (metaTheme) metaTheme.content = currentTheme === 'dark' ? '#111820' : '#f5f7fb';
  const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
  const toggle = $('#themeToggle');
  const icon = $('#themeIcon');
  const label = $('#themeLabel');
  if (icon) icon.textContent = currentTheme === 'dark' ? '☀' : '☾';
  if (label) label.textContent = nextTheme === 'dark' ? 'Dark mode' : 'Light mode';
  if (toggle) {
    toggle.setAttribute('aria-label', `Switch to ${nextTheme} theme`);
    toggle.setAttribute('title', `Switch to ${nextTheme} theme`);
    toggle.setAttribute('aria-pressed', String(currentTheme === 'dark'));
  }
  if (persist) localStorage.setItem(THEME_KEY, currentTheme);
}
function initTheme() {
  let savedTheme = localStorage.getItem(THEME_KEY);
  if (savedTheme !== 'light' && savedTheme !== 'dark') {
    savedTheme = window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  applyTheme(savedTheme);
  $('#themeToggle')?.addEventListener('click', () => {
    const current = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
    applyTheme(current === 'dark' ? 'light' : 'dark', true);
  });
}

const locales = {
  en: {
    eyebrow: 'BANKING SCAM CHECK',
    headline: 'Stop. Check. Stay safe.',
    subhead: 'Check a suspicious banking message or link before you act.',
    privacy: 'Never enter your actual OTP, PIN, password, or complete card details into RuralShield AI.',
    messageTitle: 'Check a message',
    messagePlaceholder: 'Paste the suspicious message here',
    scanMessage: 'SCAN MESSAGE',
    urlTitle: 'Check a link',
    urlPlaceholder: 'Enter suspicious URL',
    scanUrl: 'CHECK URL',
    emptyMessage: 'Enter a message to scan.',
    emptyUrl: 'Enter a URL to scan.',
  },
  hi: {
    eyebrow: 'बैंकिंग धोखाधड़ी जाँच',
    headline: 'रुकें। जाँचें। सुरक्षित रहें।',
    subhead: 'कोई संदिग्ध बैंक संदेश या लिंक खोलने से पहले जाँचें।',
    privacy: 'RuralShield AI में अपना असली OTP, PIN, पासवर्ड या पूरा कार्ड विवरण कभी न डालें।',
    messageTitle: 'संदेश जाँचें',
    messagePlaceholder: 'संदिग्ध संदेश यहाँ पेस्ट करें',
    scanMessage: 'संदेश जाँचें',
    urlTitle: 'लिंक जाँचें',
    urlPlaceholder: 'संदिग्ध URL दर्ज करें',
    scanUrl: 'URL जाँचें',
    emptyMessage: 'जाँचने के लिए संदेश दर्ज करें।',
    emptyUrl: 'जाँचने के लिए URL दर्ज करें।',
  },
  ta: {
    eyebrow: 'வங்கி மோசடி சோதனை',
    headline: 'நிறுத்துங்கள். சரிபாருங்கள். பாதுகாப்பாக இருங்கள்.',
    subhead: 'சந்தேகமான வங்கி செய்தி அல்லது இணைப்பை செயல்படும் முன் சரிபாருங்கள்.',
    privacy: 'உங்கள் உண்மையான OTP, PIN, கடவுச்சொல் அல்லது முழு அட்டை விவரங்களை RuralShield AI-ல் உள்ளிட வேண்டாம்.',
    messageTitle: 'செய்தியைச் சரிபார்க்கவும்',
    messagePlaceholder: 'சந்தேகமான செய்தியை இங்கே ஒட்டவும்',
    scanMessage: 'செய்தியை சோதிக்கவும்',
    urlTitle: 'இணைப்பைச் சரிபார்க்கவும்',
    urlPlaceholder: 'சந்தேகமான URL',
    scanUrl: 'URL சோதிக்கவும்',
    emptyMessage: 'சோதிக்க ஒரு செய்தியை உள்ளிடவும்.',
    emptyUrl: 'சோதிக்க ஒரு URL-ஐ உள்ளிடவும்.',
  },
};

function applyLocale(language) {
  const dict = locales[language] || locales.en;
  $$('[data-i18n]').forEach((element) => {
    const value = dict[element.dataset.i18n];
    if (value) element.textContent = value;
  });
  $$('[data-i18n-placeholder]').forEach((element) => {
    const value = dict[element.dataset.i18nPlaceholder];
    if (value) element.placeholder = value;
  });
  document.documentElement.lang = language;
}

const languageSelect = $('#language');
[['en', 'English'], ['hi', 'हिन्दी'], ['ta', 'தமிழ்']].forEach(([value, name]) => languageSelect?.add(new Option(name, value)));
languageSelect?.addEventListener('change', () => {
  applyLocale(languageSelect.value);
  localStorage.setItem(LANGUAGE_KEY, languageSelect.value);
});

/* =========================================
   Router & Transition System
   ========================================= */
const ROUTES = {
  '#scan': 'scan',
  '#history': 'history',
  '#dashboard': 'dashboard',
  '#login': 'login',
  '#signup': 'signup',
  '#verify': 'verify',
};
const AUTH_ROUTES = new Set(['login', 'signup', 'verify']);
const PROTECTED_ROUTES = new Set(['history', 'dashboard']);

function authToken() {
  return sessionStorage.getItem('ruralshield_id_token') || '';
}

let transitionFrame = 0;
let currentRouteHash = null;

function navigateTo(rawHash) {
  const hash = Object.prototype.hasOwnProperty.call(ROUTES, rawHash) ? rawHash : '#scan';
  const viewId = ROUTES[hash];
  if (PROTECTED_ROUTES.has(viewId) && !authToken()) {
    if (window.location.hash !== '#login') window.location.hash = '#login';
    return;
  }
  if (AUTH_ROUTES.has(viewId) && authToken()) {
    navigateTo('#scan');
    return;
  }
  if (window.location.hash !== hash) window.history.pushState(null, '', hash);
  const targetView = document.getElementById(viewId);
  if (!targetView) return;
  $$('nav button').forEach((button) => {
    const active = button.dataset.view === viewId;
    button.classList.toggle('nav-active', active);
    if (active) button.setAttribute('aria-current', 'page');
    else button.removeAttribute('aria-current');
  });
  const sameRoute = currentRouteHash === hash && targetView.classList.contains('active');
  currentRouteHash = hash;
  if (transitionFrame) cancelAnimationFrame(transitionFrame);
  $$('.view').forEach((view) => view.classList.remove('active', 'visible'));
  targetView.classList.add('active');
  transitionFrame = requestAnimationFrame(() => {
    transitionFrame = 0;
    if (targetView.classList.contains('active')) targetView.classList.add('visible');
  });
  if (!sameRoute) onViewActivated(viewId);
}
function onViewActivated(viewId) {
  if (viewId === 'history') loadHistory();
  if (viewId === 'dashboard') loadStats();
}

window.addEventListener('hashchange', () => navigateTo(window.location.hash || '#scan'));
window.addEventListener('popstate', () => navigateTo(window.location.hash || '#scan'));
window.navigate = navigateTo;

$$('nav button').forEach((button) => {
  button.addEventListener('click', () => {
    navigateTo(`#${button.dataset.view}`);
  });
});

/* =========================================
   Demo Examples
   ========================================= */
const demos = [
  ['Legitimate transaction', 'INR 1,250 debited from your account at ABC Store. If this was not you, call the number on the back of your card.'],
  ['Fake KYC', 'URGENT: Your bank KYC expires today. Verify now at http://bank-kyc-secure.example and enter OTP to avoid account block.'],
  ['Account blocking', 'Your account will be suspended in 2 hours. Confirm PIN immediately to reactivate.'],
  ['UPI scam', 'Payment failed. Enter UPI PIN at http://upi-refund.example to receive refund.'],
  ['Lottery scam', 'Congratulations! You won ₹5 lakh. Pay processing fee now to claim reward.'],
  ['Fake loan', 'Instant loan approved! Pay ₹999 verification charge and share OTP to release funds.'],
  ['Suspicious URL', 'https://sbi-secure-login.example.com.verify-now.example'],
  ['Subtle phishing', 'We noticed a profile issue. Please review your banking details using the attached link before your next transaction.'],
  ['Security reminder', 'Security reminder: our bank will never ask you to share your OTP, PIN, or password by message.'],
];

demos.forEach(([name, text]) => {
  const button = document.createElement('button');
  button.className = 'chip';
  button.type = 'button';
  button.textContent = name;
  button.addEventListener('click', () => {
    const input = $('#message');
    if (input) {
      input.value = text;
      input.focus();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  });
  $('#demoExamples')?.appendChild(button);
});

/* =========================================
   API Requests & Scan Engine
   ========================================= */
async function request(path, options = {}) {
  if (!API) throw new Error('API URL is not configured. Deploy with SAM, then configure runtime-config.js.');
  const token = authToken();
  const headers = {
    'content-type': 'application/json',
    ...(token ? { authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };
  const response = await fetch(API + path, { ...options, headers });
  let body = {};
  try { body = await response.json(); } catch { /* empty */ }
  if (!response.ok) {
    if (response.status === 401 && token) window.RuralShieldAuth?.handleSessionExpired?.();
    throw new Error(body.message || body.error || `Request failed (${response.status})`);
  }
  return body;
}

function escapeHtml(value = '') {
  return String(value).replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[character]));
}

function showResult(result) {
  const reasons = (result.reasons || [])
    .map((item) => `<li>${escapeHtml(typeof item === 'string' ? item : item.reason)}</li>`)
    .join('');
  const mitigating = (result.mitigating_signals || [])
    .map((item) => `<li>${escapeHtml(item.reason || '')}</li>`)
    .join('');
  const aiNote = result.bedrock_fallback_reason === 'public_access_disabled'
    ? '<p class="muted">AI explanation is enabled after sign-in; this result used local security signals.</p>'
    : '';
  const rawClassification = String(result.classification || 'SUSPICIOUS').toUpperCase();
  const status = ['SAFE', 'SUSPICIOUS', 'PHISHING'].includes(rawClassification)
    ? rawClassification.toLowerCase()
    : 'suspicious';
  const score = Math.max(0, Math.min(100, Math.round(Number(result.risk_score) || 0)));
  const canGiveFeedback = result.persisted === true && Boolean(authToken());
  const feedbackMarkup = canGiveFeedback
    ? `<div class="feedback" aria-label="Detection feedback">
        <p><b>Was this result useful?</b></p>
        <button class="secondary compact" type="button" data-feedback="helpful" data-scan-id="${escapeHtml(result.scan_id || '')}">Yes</button>
        <button class="secondary compact" type="button" data-feedback="incorrect" data-scan-id="${escapeHtml(result.scan_id || '')}">No / incorrect</button>
        <span id="feedbackStatus" role="status" aria-live="polite"></span>
      </div>`
    : authToken()
      ? '<p class="muted">This scan could not be saved, so feedback is unavailable for this result.</p>'
      : '<p class="muted">This anonymous scan was not saved to private history. <a class="link" href="#login">Sign in</a> before future scans to save history and submit feedback.</p>';

  const resultContainer = $('#result');
  resultContainer.classList.remove('hidden');
  resultContainer.innerHTML = `
    <div class="result-top">
      <div>
        <p class="eyebrow">SCAN RESULT</p>
        <div class="status ${status}" role="status">${escapeHtml(result.classification)}</div>
        <p>${escapeHtml(result.summary || 'Review the signals below before taking action.')}</p>
        ${aiNote}
      </div>
      <div class="score">
        <span>Risk score</span><br>
        <strong>${score}/100</strong><br>
        <span>Decision strength: ${escapeHtml(result.confidence_level || 'LOW')}</span>
      </div>
    </div>
    <div class="meter ${status}" role="progressbar" aria-label="Risk score" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${score}" aria-valuetext="${score} out of 100">
      <span></span>
    </div>
    <div class="result-grid">
      <div>
        <h3>Why?</h3>
        <ul>${reasons || '<li>No strong phishing signal was found.</li>'}</ul>
        ${mitigating ? `<h3>Risk-reducing signals</h3><ul>${mitigating}</ul>` : ''}
        <p><b>Category:</b> ${escapeHtml(result.scam_category || 'Unknown')}</p>
        <p><b>Language:</b> ${escapeHtml(result.detected_language || 'unknown')}</p>
        <p><b>Model:</b> ${escapeHtml(result.model_version || 'unknown')}</p>
      </div>
      <div>
        <h3>Recommended action</h3>
        <p class="action">${escapeHtml(result.recommendation || 'Do not share sensitive banking credentials. Use an official bank channel if unsure.')}</p>
        <h3>Decision architecture</h3>
        <p>Final risk uses ML + rules + passive URL evidence. Generative AI only adds contextual explanation.</p>
${feedbackMarkup}
      </div>
    </div>`;

  // Animate the risk meter bar smoothly from 0% to score%
  requestAnimationFrame(() => {
    const span = resultContainer.querySelector('.meter span');
    if (span) {
      span.style.width = '0%';
      requestAnimationFrame(() => {
        span.style.width = `${score}%`;
      });
    }
  });

  $$('[data-feedback]').forEach((button) => {
    button.addEventListener('click', async () => {
      const scanId = button.dataset.scanId;
      const statusText = $('#feedbackStatus');
      if (!scanId) {
        if (statusText) statusText.textContent = 'Feedback is available after sign-in.';
        return;
      }
      button.disabled = true;
      try {
        await request('/feedback', { method: 'POST', body: JSON.stringify({ scan_id: scanId, feedback: button.dataset.feedback }) });
        if (statusText) statusText.textContent = 'Thanks! Feedback recorded.';
      } catch (error) {
        if (statusText) statusText.textContent = error.message;
      } finally {
        button.disabled = false;
      }
    });
  });

  resultContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function scan(type, value, button) {
  const input = type === 'url' ? $('#url') : $('#message');
  const cleanValue = typeof value === 'string' ? value.trim() : '';
  const inputError = $('#scanInputError');
  if (!cleanValue) {
    if (inputError) {
      const language = locales[languageSelect?.value] || locales.en;
      inputError.textContent = type === 'url' ? language.emptyUrl : language.emptyMessage;
      inputError.classList.remove('hidden');
    }
    input?.focus();
    return;
  }
  if (inputError) inputError.classList.add('hidden');
  button.disabled = true;
  const originalHtml = button.innerHTML;
  button.innerHTML = '<span class="spinner"></span> CHECKING…';

  try {
    const scanPath = authToken() ? '/scan-authenticated' : '/scan';
    const result = await request(scanPath, {
      method: 'POST',
      body: JSON.stringify({ type, text: cleanValue, language: languageSelect?.value || 'en' }),
    });
    showResult(result);
  } catch (error) {
    const resultContainer = $('#result');
    resultContainer.classList.remove('hidden');
    resultContainer.innerHTML = `
      <h2>Could not complete scan</h2>
      <p>${escapeHtml(error.message)}</p>
      <button class="secondary" id="retryScan" type="button">Retry</button>
    `;
    $('#retryScan')?.addEventListener('click', () => scan(type, value, button));
  } finally {
    button.disabled = false;
    button.innerHTML = originalHtml;
  }
}

$('#scanMessage')?.addEventListener('click', () => scan('message', $('#message')?.value || '', $('#scanMessage')));
$('#scanUrl')?.addEventListener('click', () => scan('url', $('#url')?.value || '', $('#scanUrl')));
$('#message')?.addEventListener('input', () => $('#scanInputError')?.classList.add('hidden'));
$('#url')?.addEventListener('input', () => $('#scanInputError')?.classList.add('hidden'));

function formatTimestamp(value) {
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return String(value || '—');
  const dateLocales = { en: 'en-IN', hi: 'hi-IN', ta: 'ta-IN' };
  return new Intl.DateTimeFormat(dateLocales[languageSelect?.value] || 'en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

/* =========================================
   History & Statistics
   ========================================= */
async function loadHistory() {
  const element = $('#historyContent');
  if (!element) return;
  element.innerHTML = '<p class="muted">Loading scan history…</p>';

  try {
    const data = await request('/history');
    const rows = Array.isArray(data.items) ? data.items : [];
    element.innerHTML = rows.length
      ? `<div class="table-wrap"><table class="table">
          <thead>
            <tr>
              <th>TIME</th>
              <th>TYPE</th>
              <th>RESULT</th>
              <th>RISK</th>
              <th>CATEGORY</th>
              <th>MODEL</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map((row) => `
              <tr>
                <td><time datetime="${escapeHtml(row.timestamp)}">${escapeHtml(formatTimestamp(row.timestamp))}</time></td>
                <td>${escapeHtml(row.input_type)}</td>
                <td class="badge">${escapeHtml(row.classification)}</td>
                <td>${escapeHtml(row.risk_score)}</td>
                <td>${escapeHtml(row.scam_category)}</td>
                <td>${escapeHtml(row.model_version || 'unknown')}</td>
              </tr>
            `).join('')}
          </tbody>
        </table></div>`
      : '<div class="empty">No scans stored yet.</div>';
  } catch (error) {
    const detail = error.message || 'Could not load scan history.';
    const hint = detail.includes('API URL is not configured')
      ? 'Configure the API endpoint in the deployment runtime configuration.'
      : 'If your sign-in session expired, sign in again and retry.';
    element.innerHTML = `<div class="empty"><p>${escapeHtml(detail)}</p><p class="muted">${escapeHtml(hint)}</p><button class="secondary compact" id="retryHistory" type="button">Try again</button></div>`;
    $('#retryHistory')?.addEventListener('click', loadHistory);
  }
}

async function loadStats() {
  const element = $('#statsContent');
  if (!element) return;
  element.innerHTML = '<div class="panel"><p class="muted">Loading dashboard…</p></div>';

  try {
    const data = await request('/statistics');
    const categories = data.scam_categories || {};
    element.innerHTML = `
      <div class="metrics">
        <div class="metric"><span>Total scans</span><strong>${data.total_scans || 0}</strong></div>
        <div class="metric"><span>Safe</span><strong>${data.safe || 0}</strong></div>
        <div class="metric"><span>Suspicious</span><strong>${data.suspicious || 0}</strong></div>
        <div class="metric"><span>Phishing</span><strong>${data.phishing || 0}</strong></div>
        <div class="metric"><span>Phishing %</span><strong>${Number(data.phishing_percentage || 0).toFixed(1)}%</strong></div>
      </div>
      <div class="panel">
        <h2>Scam categories</h2>
        ${Object.entries(categories).map(([key, value]) => `<p>${escapeHtml(key)} — <b>${escapeHtml(value)}</b></p>`).join('') || '<p>No stored data yet.</p>'}
        ${data.statistics_truncated ? '<p class="muted">Statistics are capped for safety.</p>' : ''}
      </div>`;
  } catch (error) {
    const detail = error.message || 'Could not load dashboard statistics.';
    const hint = detail.includes('API URL is not configured')
      ? 'Configure the API endpoint in the deployment runtime configuration.'
      : 'If your sign-in session expired, sign in again and retry.';
    element.innerHTML = `<div class="panel"><div class="empty"><p>${escapeHtml(detail)}</p><p class="muted">${escapeHtml(hint)}</p><button class="secondary compact" id="retryStats" type="button">Try again</button></div></div>`;
    $('#retryStats')?.addEventListener('click', loadStats);
  }
}

$('#refreshHistory')?.addEventListener('click', loadHistory);
$('#refreshStats')?.addEventListener('click', loadStats);

// Initialize preferences before showing the first route.
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  const savedLanguage = localStorage.getItem(LANGUAGE_KEY);
  const initialLanguage = Object.prototype.hasOwnProperty.call(locales, savedLanguage) ? savedLanguage : 'en';
  if (languageSelect) languageSelect.value = initialLanguage;
  applyLocale(initialLanguage);
  navigateTo(window.location.hash || '#scan');
  window.RuralShieldAuth?.updateAuthHeader();
});
