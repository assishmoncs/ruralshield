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

$$('nav button').forEach((button) => {
  button.addEventListener('click', () => {
    $$('.view').forEach((view) => view.classList.remove('active'));
    $(`#${button.dataset.view}`)?.classList.add('active');
    if (button.dataset.view === 'history') loadHistory();
    if (button.dataset.view === 'dashboard') loadStats();
  });
});

$('#authToggle')?.addEventListener('click', () => {
  const panel = $('#authPanel');
  if (!panel) return;
  const hidden = panel.classList.toggle('hidden');
  $('#authToggle').setAttribute('aria-expanded', String(!hidden));
  if (!hidden) panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
});
$('#closeAuth')?.addEventListener('click', () => {
  $('#authPanel')?.classList.add('hidden');
  $('#authToggle')?.setAttribute('aria-expanded', 'false');
});

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
    $('#message').value = text;
    $('#message').focus();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  $('#demoExamples')?.appendChild(button);
});

function authToken() {
  return sessionStorage.getItem('ruralshield_access_token') || '';
}

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
  try { body = await response.json(); } catch { /* empty response */ }
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
  const status = (result.classification || 'SUSPICIOUS').toLowerCase();
  $('#result').classList.remove('hidden');
  $('#result').innerHTML = `
    <div class="result-top">
      <div>
        <p class="eyebrow">SCAN RESULT</p>
        <div class="status ${status}" role="status">${escapeHtml(result.classification)}</div>
        <p>${escapeHtml(result.summary || 'Review the signals below before taking action.')}</p>
      </div>
      <div class="score">
        <span>Risk score</span><br>
        <strong>${Math.round(result.risk_score || 0)}/100</strong><br>
        <span>Decision strength: ${escapeHtml(result.confidence_level || 'LOW')}</span>
      </div>
    </div>
    <div class="meter" aria-label="Risk score meter"><span style="width:${Math.max(0, Math.min(100, result.risk_score || 0))}%"></span></div>
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
          <button class="secondary" type="button" data-feedback="helpful" data-scan-id="${escapeHtml(result.scan_id || '')}">Yes</button>
          <button class="secondary" type="button" data-feedback="incorrect" data-scan-id="${escapeHtml(result.scan_id || '')}">No / incorrect</button>
          <span id="feedbackStatus" role="status"></span>
        </div>
      </div>
    </div>`;

  $$('[data-feedback]').forEach((button) => {
    button.addEventListener('click', async () => {
      const scanId = button.dataset.scanId;
      const status = $('#feedbackStatus');
      if (!scanId) { status.textContent = 'Feedback is unavailable for this scan.'; return; }
      button.disabled = true;
      try {
        await request('/feedback', { method: 'POST', body: JSON.stringify({ scan_id: scanId, feedback: button.dataset.feedback }) });
        status.textContent = 'Thanks. Feedback recorded.';
      } catch (error) {
        status.textContent = error.message;
      } finally {
        button.disabled = false;
      }
    });
  });
  $('#result').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function scan(type, value, button) {
  if (!value.trim()) return;
  button.disabled = true;
  const old = button.textContent;
  button.textContent = 'CHECKING…';
  try {
    showResult(await request('/scan', {
      method: 'POST',
      body: JSON.stringify({ type, text: value, language: languageSelect?.value || 'en' }),
    }));
  } catch (error) {
    $('#result').classList.remove('hidden');
    $('#result').innerHTML = `<h2>Could not complete scan</h2><p>${escapeHtml(error.message)}</p><button class="secondary" id="retryScan" type="button">Retry</button>`;
    $('#retryScan')?.addEventListener('click', () => scan(type, value, button));
  } finally {
    button.disabled = false;
    button.textContent = old;
  }
}

$('#scanMessage')?.addEventListener('click', () => scan('message', $('#message').value, $('#scanMessage')));
$('#scanUrl')?.addEventListener('click', () => scan('url', $('#url').value, $('#scanUrl')));

async function loadHistory() {
  const element = $('#historyContent');
  element.innerHTML = '<p>Loading…</p>';
  try {
    const data = await request('/history');
    const rows = data.items || [];
    element.innerHTML = rows.length
      ? `<table class="table"><thead><tr><th>TIME</th><th>TYPE</th><th>RESULT</th><th>RISK</th><th>CATEGORY</th><th>MODEL</th></tr></thead><tbody>${rows.map((row) => `<tr><td>${escapeHtml(row.timestamp)}</td><td>${escapeHtml(row.input_type)}</td><td class="badge">${escapeHtml(row.classification)}</td><td>${escapeHtml(row.risk_score)}</td><td>${escapeHtml(row.scam_category)}</td><td>${escapeHtml(row.model_version || 'unknown')}</td></tr>`).join('')}</tbody></table>`
      : '<div class="empty">No scans stored yet.</div>';
  } catch (error) {
    element.innerHTML = `<div class="empty">${escapeHtml(error.message)}. Sign in is required for private history.</div>`;
  }
}

async function loadStats() {
  const element = $('#statsContent');
  element.innerHTML = '<div class="panel">Loading…</div>';
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
      <div class="panel"><h2>Scam categories</h2>${Object.entries(categories).map(([key, value]) => `<p>${escapeHtml(key)} — <b>${escapeHtml(value)}</b></p>`).join('') || '<p>No stored data yet.</p>'}${data.statistics_truncated ? '<p>Statistics are capped for safety.</p>' : ''}</div>`;
  } catch (error) {
    element.innerHTML = `<div class="panel">${escapeHtml(error.message)}. Sign in is required for private statistics.</div>`;
  }
}

$('#refreshHistory')?.addEventListener('click', loadHistory);
$('#refreshStats')?.addEventListener('click', loadStats);
applyLocale('en');
