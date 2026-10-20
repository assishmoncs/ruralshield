(() => {
  const cfg = window.RURALSHIELD_CONFIG || {};
  const region = cfg.cognitoRegion || '';
  const clientId = cfg.cognitoClientId || '';
  const tokenKey = 'ruralshield_id_token';
  const MIN_PASSWORD_LENGTH = 12;

  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => [...document.querySelectorAll(selector)];

  function setMessage(elementId, text, type = 'info') {
    const el = $(elementId);
    if (!el) return;
    el.textContent = text;
    el.dataset.type = type;
    el.classList.toggle('hidden', !text);
  }

  function updateAuthHeader() {
    const authAction = $('#authAction');
    if (!authAction) return;

    const token = sessionStorage.getItem(tokenKey);
    const email = sessionStorage.getItem('ruralshield_user_email') || '';
    authAction.onclick = null;
    authAction.textContent = '';

    if (token) {
      const avatar = document.createElement('span');
      avatar.className = 'user-avatar';
      avatar.textContent = (email ? email[0] : 'U').toUpperCase();
      avatar.setAttribute('aria-hidden', 'true');
      authAction.append(avatar, document.createTextNode(' Sign out'));
      authAction.removeAttribute('href');
      authAction.setAttribute('aria-label', 'Sign out');
      authAction.onclick = (event) => {
        event.preventDefault();
        signOut();
      };
    } else {
      authAction.textContent = 'Sign in';
      authAction.setAttribute('href', '#login');
      authAction.setAttribute('aria-label', 'Sign in');
    }
  }
  function setAuthenticated(idToken, email = '', accessToken = '') {
    sessionStorage.setItem(tokenKey, idToken);
    if (accessToken) sessionStorage.setItem('ruralshield_access_token', accessToken);
    if (email) sessionStorage.setItem('ruralshield_user_email', email);
    updateAuthHeader();
    if (window.navigate) {
      window.navigate('#scan');
    }
  }

  function clearAuthenticated() {
    sessionStorage.removeItem(tokenKey);
    sessionStorage.removeItem('ruralshield_access_token');
    sessionStorage.removeItem('ruralshield_user_email');
    updateAuthHeader();
  }

  async function cognitoRequest(target, body) {
    if (!region || !clientId) {
      throw new Error('Authentication is not configured for this deployment. Please set Cognito configuration in runtime-config.js.');
    }
    const response = await fetch(`https://cognito-idp.${region}.amazonaws.com/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-amz-json-1.1',
        'X-Amz-Target': `AWSCognitoIdentityProviderService.${target}`,
      },
      body: JSON.stringify({ ClientId: clientId, ...body }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.message || `Authentication request failed (${response.status})`);
    }
    return data;
  }

  async function handleSignUp(e) {
    e.preventDefault();
    const email = $('#signupEmail')?.value.trim().toLowerCase();
    const password = $('#signupPassword')?.value || '';
    const submitBtn = $('#signUpSubmit');

    if (!email || !password) {
      return setMessage('#signupMessage', 'Please provide both email and password.', 'error');
    }
    if (!$('#signupEmail')?.checkValidity()) {
      return setMessage('#signupMessage', 'Enter a valid email address.', 'error');
    }
    const strongPassword = password.length >= MIN_PASSWORD_LENGTH &&
      /[A-Z]/.test(password) && /[a-z]/.test(password) &&
      /[0-9]/.test(password) && /[^A-Za-z0-9]/.test(password);
    if (!strongPassword) {
      return setMessage('#signupMessage', 'Use at least 12 characters with uppercase and lowercase letters, a number, and a symbol.', 'error');
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span> CREATING ACCOUNT…';
    }
    setMessage('#signupMessage', '', 'info');

    try {
      await cognitoRequest('SignUp', {
        Username: email,
        Password: password,
        UserAttributes: [{ Name: 'email', Value: email }],
      });
      sessionStorage.setItem('ruralshield_pending_email', email);
      const display = $('#verifyEmailDisplay');
      if (display) display.textContent = email;
      const hidden = $('#verifyEmailHidden');
      if (hidden) hidden.value = email;

      setMessage('#signupMessage', '', 'info');
      if (window.navigate) {
        window.navigate('#verify');
      }
    } catch (error) {
      setMessage('#signupMessage', error.message, 'error');
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'CREATE ACCOUNT';
      }
    }
  }

  async function handleConfirmSignUp(e) {
    e.preventDefault();
    const email = $('#verifyEmailHidden')?.value.trim().toLowerCase() ||
                  sessionStorage.getItem('ruralshield_pending_email') || '';
    const code = $('#verifyCode')?.value.trim();
    const submitBtn = $('#verifySubmit');

    if (!email || !code) {
      return setMessage('#verifyMessage', 'Please enter your verification code.', 'error');
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span> VERIFYING…';
    }

    try {
      await cognitoRequest('ConfirmSignUp', { Username: email, ConfirmationCode: code });
      sessionStorage.removeItem('ruralshield_pending_email');
      setMessage('#loginMessage', 'Email verified successfully! Please sign in.', 'success');
      const loginEmail = $('#loginEmail');
      if (loginEmail) loginEmail.value = email;
      if (window.navigate) {
        window.navigate('#login');
      }
    } catch (error) {
      setMessage('#verifyMessage', error.message, 'error');
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'CONFIRM EMAIL';
      }
    }
  }

  async function handleSignIn(e) {
    e.preventDefault();
    const email = $('#loginEmail')?.value.trim().toLowerCase();
    const password = $('#loginPassword')?.value || '';
    const submitBtn = $('#signInSubmit');

    if (!email || !password) {
      return setMessage('#loginMessage', 'Please enter your email and password.', 'error');
    }
    if (!$('#loginEmail')?.checkValidity()) {
      return setMessage('#loginMessage', 'Enter a valid email address.', 'error');
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span> SIGNING IN…';
    }

    try {
      const result = await cognitoRequest('InitiateAuth', {
        AuthFlow: 'USER_PASSWORD_AUTH',
        AuthParameters: { USERNAME: email, PASSWORD: password },
      });
      const idToken = result.AuthenticationResult?.IdToken;
      if (!idToken) throw new Error('Authentication succeeded but no ID token was returned.');
      const accessToken = result.AuthenticationResult?.AccessToken || '';
      setMessage('#loginMessage', '', 'info');
      setAuthenticated(idToken, email, accessToken);
    } catch (error) {
      setMessage('#loginMessage', error.message, 'error');
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'SIGN IN';
      }
    }
  }

  function revokeCognitoSession(accessToken) {
    if (!accessToken || !region) return;
    fetch(`https://cognito-idp.${region}.amazonaws.com/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-amz-json-1.1',
        'X-Amz-Target': 'AWSCognitoIdentityProviderService.GlobalSignOut',
      },
      body: JSON.stringify({ AccessToken: accessToken }),
    }).catch(() => {
      // Local sign-out has already completed; server revocation is best effort.
    });
  }

  function signOut() {
    const accessToken = sessionStorage.getItem('ruralshield_access_token') || '';
    clearAuthenticated();
    revokeCognitoSession(accessToken);
    setMessage('#loginMessage', 'You have been signed out on this device.', 'info');
    if (window.navigate) window.navigate('#login');
  }

  function handleSessionExpired() {
    clearAuthenticated();
    setMessage('#loginMessage', 'Your session has expired. Please sign in again.', 'error');
    if (window.navigate) window.navigate('#login');
  }

  function setupPasswordToggles() {
    $$('.password-toggle').forEach((btn) => {
      btn.addEventListener('click', () => {
        const input = btn.closest('.password-wrapper')?.querySelector('input');
        if (!input) return;
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        btn.textContent = isPassword ? '🙈' : '👁';
        btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
      });
    });
  }

  function init() {
    $('#signupForm')?.addEventListener('submit', handleSignUp);
    $('#verifyForm')?.addEventListener('submit', handleConfirmSignUp);
    $('#loginForm')?.addEventListener('submit', handleSignIn);

    setupPasswordToggles();
    updateAuthHeader();

    const pendingEmail = sessionStorage.getItem('ruralshield_pending_email');
    if (pendingEmail) {
      const display = $('#verifyEmailDisplay');
      if (display) display.textContent = pendingEmail;
      const hidden = $('#verifyEmailHidden');
      if (hidden) hidden.value = pendingEmail;
    }
  }

  window.RuralShieldAuth = {
    init,
    signOut,
    isAuthenticated: () => Boolean(sessionStorage.getItem(tokenKey)),
    getToken: () => sessionStorage.getItem(tokenKey) || '',
    getUserEmail: () => sessionStorage.getItem('ruralshield_user_email') || '',
    handleSessionExpired,
    updateAuthHeader,
  };

  document.addEventListener('DOMContentLoaded', init);
})();
