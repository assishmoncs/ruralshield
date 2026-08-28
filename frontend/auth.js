(() => {
  const cfg = window.RURALSHIELD_CONFIG || {};
  const region = cfg.cognitoRegion || '';
  const clientId = cfg.cognitoClientId || '';
  const tokenKey = 'ruralshield_access_token';

  const $ = (selector) => document.querySelector(selector);

  function setMessage(text, type = 'info') {
    const el = $('#authMessage');
    if (!el) return;
    el.textContent = text;
    el.dataset.type = type;
  }

  function setAuthenticated(accessToken) {
    sessionStorage.setItem(tokenKey, accessToken);
    $('#authForms')?.classList.add('hidden');
    $('#authSession')?.classList.remove('hidden');
    const email = sessionStorage.getItem('ruralshield_user_email') || '';
    if ($('#authUser')) $('#authUser').textContent = email || 'Signed in';
    setMessage('Signed in. Private history and statistics are available.', 'success');
  }

  function clearAuthenticated() {
    sessionStorage.removeItem(tokenKey);
    sessionStorage.removeItem('ruralshield_user_email');
    $('#authForms')?.classList.remove('hidden');
    $('#authSession')?.classList.add('hidden');
  }

  async function cognitoRequest(target, body) {
    if (!region || !clientId) throw new Error('Authentication is not configured for this deployment.');
    const response = await fetch(`https://cognito-idp.${region}.amazonaws.com/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-amz-json-1.1',
        'X-Amz-Target': `AWSCognitoIdentityProviderService.${target}`,
      },
      body: JSON.stringify({ ClientId: clientId, ...body }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.message || `Authentication request failed (${response.status})`);
    return data;
  }

  async function signUp() {
    const email = $('#authEmail')?.value.trim().toLowerCase();
    const password = $('#authPassword')?.value || '';
    if (!email || !password) return setMessage('Enter an email and password.', 'error');
    if (password.length < 8) return setMessage('Password must contain at least 8 characters.', 'error');
    try {
      await cognitoRequest('SignUp', {
        Username: email,
        Password: password,
        UserAttributes: [{ Name: 'email', Value: email }],
      });
      sessionStorage.setItem('ruralshield_pending_email', email);
      $('#confirmEmail').value = email;
      $('#confirmForm')?.classList.remove('hidden');
      setMessage('Account created. Enter the verification code sent to your email.', 'success');
    } catch (error) {
      setMessage(error.message, 'error');
    }
  }

  async function confirmSignUp() {
    const email = $('#confirmEmail')?.value.trim().toLowerCase();
    const code = $('#confirmCode')?.value.trim();
    if (!email || !code) return setMessage('Enter the email and verification code.', 'error');
    try {
      await cognitoRequest('ConfirmSignUp', { Username: email, ConfirmationCode: code });
      sessionStorage.removeItem('ruralshield_pending_email');
      $('#confirmForm')?.classList.add('hidden');
      $('#authEmail').value = email;
      setMessage('Email verified. Sign in to continue.', 'success');
    } catch (error) {
      setMessage(error.message, 'error');
    }
  }

  async function signIn() {
    const email = $('#authEmail')?.value.trim().toLowerCase();
    const password = $('#authPassword')?.value || '';
    if (!email || !password) return setMessage('Enter an email and password.', 'error');
    try {
      const result = await cognitoRequest('InitiateAuth', {
        AuthFlow: 'USER_PASSWORD_AUTH',
        AuthParameters: { USERNAME: email, PASSWORD: password },
      });
      const accessToken = result.AuthenticationResult?.AccessToken;
      if (!accessToken) throw new Error('Authentication succeeded but no access token was returned.');
      sessionStorage.setItem('ruralshield_user_email', email);
      setAuthenticated(accessToken);
    } catch (error) {
      setMessage(error.message, 'error');
    }
  }

  function signOut() {
    clearAuthenticated();
    setMessage('Signed out.', 'info');
  }

  function init() {
    $('#signUpButton')?.addEventListener('click', signUp);
    $('#confirmButton')?.addEventListener('click', confirmSignUp);
    $('#signInButton')?.addEventListener('click', signIn);
    $('#signOutButton')?.addEventListener('click', signOut);

    const existing = sessionStorage.getItem(tokenKey);
    if (existing) setAuthenticated(existing);
  }

  window.RuralShieldAuth = { init, signOut };
  document.addEventListener('DOMContentLoaded', init);
})();
