"""Licence lock for the desktop exe: a licence key only works on the PC it was issued for.

Keys are signed with a private key that stays on the developer's PC (see license_tool.py);
the exe only contains the public key below, so it can check keys but never create them.
"""
import base64
import datetime
import hashlib
import html
import os
import uuid

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

PUBLIC_KEY = 'OpSjl0fc9JLkrUKeERvoZ03gFBy6Cjn-AK55sglnZLc'  # filled in by: python license_tool.py init

LICENSE_FILE = os.path.join(
    os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'SAI Calibration', 'license.key'
)


def machine_code():
    """Short code identifying this Windows installation, e.g. 3F9A-0C21-7B44-E1D8."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Cryptography', 0,
                            winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            raw = winreg.QueryValueEx(key, 'MachineGuid')[0]
    except OSError:
        raw = str(uuid.getnode())
    digest = hashlib.sha256(('SAI-CAL|' + raw).encode()).hexdigest().upper()[:16]
    return '-'.join(digest[i:i + 4] for i in range(0, 16, 4))


def b64encode(data):
    return base64.urlsafe_b64encode(data).decode().rstrip('=')


def b64decode(text):
    return base64.urlsafe_b64decode(text + '=' * (-len(text) % 4))


def verify(key, code=None):
    """Return (ok, message)."""
    key = ''.join((key or '').split())
    try:
        body, signature = key.split('.')
        payload = b64decode(body)
        Ed25519PublicKey.from_public_bytes(b64decode(PUBLIC_KEY)).verify(b64decode(signature), payload)
        licensed_code, name, expiry = payload.decode().split('|')
    except (ValueError, InvalidSignature, UnicodeDecodeError):
        return False, 'This licence key is not valid. Please check that it was copied completely.'

    if licensed_code != (code or machine_code()):
        return False, 'This licence key was issued for a different computer.'
    if expiry:
        expiry_date = datetime.date.fromisoformat(expiry)
        if datetime.date.today() > expiry_date:
            return False, (f'This licence expired on {expiry_date:%d-%m-%Y}. '
                           'Please contact SAI Accurate Instruments for renewal.')
        return True, f'Licensed to {name} until {expiry_date:%d-%m-%Y}'
    return True, f'Licensed to {name}'


def check():
    """Check the saved licence. Returns (ok, message); message is empty before first activation."""
    if not os.path.exists(LICENSE_FILE):
        return False, ''
    with open(LICENSE_FILE, encoding='utf-8') as f:
        return verify(f.read())


def activate(key):
    ok, message = verify(key)
    if ok:
        os.makedirs(os.path.dirname(LICENSE_FILE), exist_ok=True)
        with open(LICENSE_FILE, 'w', encoding='utf-8') as f:
            f.write(''.join(key.split()))
    return ok, message


ACTIVATION_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: Arial, sans-serif; margin: 0; padding: 24px 32px; background: #f4f6f9; color: #222; }
  h2 { margin: 0 0 6px; color: #0d3b66; }
  p { margin: 6px 0 14px; line-height: 1.4; }
  label { font-weight: bold; display: block; margin-bottom: 6px; }
  .code-row { display: flex; gap: 8px; margin-bottom: 18px; }
  #code { flex: 1; font: bold 20px Consolas, monospace; letter-spacing: 2px; padding: 8px; text-align: center;
          border: 1px solid #999; background: #fff; }
  textarea { width: 100%; box-sizing: border-box; height: 90px; font: 13px Consolas, monospace; padding: 8px;
             border: 1px solid #999; resize: none; }
  button { padding: 8px 18px; font-size: 14px; border: 0; border-radius: 4px; cursor: pointer;
           background: #0d6efd; color: #fff; }
  button:disabled { background: #888; cursor: default; }
  #message { min-height: 20px; margin-top: 12px; font-weight: bold; }
  .error { color: #c00; }
  .ok { color: #198754; }
</style>
</head>
<body>
  <h2>Activate SAI Calibration</h2>
  <p>Send the Machine Code below to SAI Accurate Instruments. You will receive a licence key for this computer.</p>
  <label for="code">Machine Code</label>
  <div class="code-row">
    <input id="code" readonly value="__CODE__">
    <button id="copy" type="button">Copy</button>
  </div>
  <label for="key">Licence Key</label>
  <textarea id="key" placeholder="Paste the licence key here"></textarea>
  <div style="margin-top:12px"><button id="activate" type="button">Activate</button></div>
  <div id="message" class="error">__MESSAGE__</div>
<script>
  const message = document.getElementById('message');
  document.getElementById('copy').addEventListener('click', function () {
    const code = document.getElementById('code');
    code.select();
    document.execCommand('copy');
    message.className = 'ok';
    message.textContent = 'Machine Code copied.';
  });
  document.getElementById('activate').addEventListener('click', function () {
    const button = this;
    const key = document.getElementById('key').value.trim();
    if (!key) {
      message.className = 'error';
      message.textContent = 'Please paste the licence key.';
      return;
    }
    button.disabled = true;
    message.className = 'ok';
    message.textContent = 'Activating, please wait...';
    window.pywebview.api.activate(key).then(function (result) {
      if (!result.ok) {
        button.disabled = false;
        message.className = 'error';
        message.textContent = result.message;
      }
    });
  });
</script>
</body>
</html>
"""


def activation_html(message=''):
    return (ACTIVATION_HTML
            .replace('__CODE__', machine_code())
            .replace('__MESSAGE__', html.escape(message)))
