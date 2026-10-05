const config = window.RURALSHIELD_CONFIG || {};
const API = (config.apiUrl || window.RURALSHIELD_API_URL || localStorage.getItem('ruralshield_api') || '').replace(/\/$/, '');
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

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
languageSelect?.addEventListener('change', () => applyLocale(languageSelect.value));

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

function navigate(rawHash) {
  const hash = rawHash || '#scan';
  const viewId = ROUTES[hash] || 'scan';

  // Guard protected routes
  if (PROTECTED_ROUTES.has(viewId) && !authToken()) {
    window.location.hash = '#login';
    return;
  }

  // Guard auth routes if already authenticated
  if (AUTH_ROUTES.has(viewId) && authToken()) {
    window.location.hash = '#scan';
    return;
  }

  const currentView = $('.view.visible');
  const targetView = $(`#${viewId}`);
  if (!targetView) return;

  // Update nav active indicator
  $$('nav button').forEach((button) => {
    button.classList.toggle('nav-active', button.dataset.view === viewId);
  });

  // Smooth transition: fade out current, then activate & fade in new view
  if (currentView && currentView !== targetView) {
    currentView.classList.remove('visible');
    setTimeout(() => {
      $$('.view').forEach((v) => v.classList.remove('active', 'visible'));
      targetView.classList.add('active');
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          targetView.classList.add('visible');
        });
      });
      onViewActivated(viewId);
    }, 180);
  } else {
    $$('.view').forEach((v) => v.classList.remove('active', 'visible'));
    targetView.classList.add('active');
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        targetView.classList.add('visible');
      });
    });
    onViewActivated(viewId);
  }

  if (window.location.hash !== hash) {
    window.history.pushState(null, '', hash);
  }
}

function onViewActivated(viewId) {
  if (viewId === 'history') loadHistory();
  if (viewId === 'dashboard') loadStats();
}

window.addEventListener('hashchange', () => navigate(window.location.hash));
window.navigate = (hash) => {
  window.location.hash = hash;
};

$$('nav button').forEach((button) => {
  button.addEventListener('click', () => {
    navigate(`#${button.dataset.view}`);
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
  if (!response.ok) throw new Error(body.message || body.error || `Request failed (${response.status})`);
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
  const status = (result.classification || 'SUSPICIOUS').toLowerCase();
  const score = Math.max(0, Math.min(100, Math.round(result.risk_score || 0)));

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
    <div class="meter ${status}" aria-label="Risk score meter">
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
        <div class="feedback" aria-label="Detection feedback">
          <p><b>Was this result useful?</b></p>
          <button class="secondary compact" type="button" data-feedback="helpful" data-scan-id="${escapeHtml(result.scan_id || '')}">Yes</button>
          <button class="secondary compact" type="button" data-feedback="incorrect" data-scan-id="${escapeHtml(result.scan_id || '')}">No / incorrect</button>
          <span id="feedbackStatus" role="status"></span>
        </div>
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
  if (!value.trim()) return;
  button.disabled = true;
  const originalHtml = button.innerHTML;
  button.innerHTML = '<span class="spinner"></span> CHECKING…';

  try {
    const result = await request('/scan', {
      method: 'POST',
      body: JSON.stringify({ type, text: value, language: languageSelect?.value || 'en' }),
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

/* =========================================
   History & Statistics
   ========================================= */
async function loadHistory() {
  const element = $('#historyContent');
  if (!element) return;
  element.innerHTML = '<p class="muted">Loading scan history…</p>';

  try {
    const data = await request('/history');
    const rows = data.items || [];
    element.innerHTML = rows.length
      ? `<table class="table">
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
                <td>${escapeHtml(row.timestamp)}</td>
                <td>${escapeHtml(row.input_type)}</td>
                <td class="badge">${escapeHtml(row.classification)}</td>
                <td>${escapeHtml(row.risk_score)}</td>
                <td>${escapeHtml(row.scam_category)}</td>
                <td>${escapeHtml(row.model_version || 'unknown')}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>`
      : '<div class="empty">No scans stored yet.</div>';
  } catch (error) {
    element.innerHTML = `<div class="empty">${escapeHtml(error.message)}. Sign in is required for private history.</div>`;
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
    element.innerHTML = `<div class="panel"><div class="empty">${escapeHtml(error.message)}. Sign in is required for private statistics.</div></div>`;
  }
}

$('#refreshHistory')?.addEventListener('click', loadHistory);
$('#refreshStats')?.addEventListener('click', loadStats);

// Initialize routing and default locale
document.addEventListener('DOMContentLoaded', () => {
  applyLocale('en');
  navigate(window.location.hash || '#scan');
  window.RuralShieldAuth?.updateAuthHeader();
});
