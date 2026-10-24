"""Run the calibration software in its own desktop window instead of a web browser.

Usage:  python desktop_app.py
Render keeps using manage.py / start.sh; nothing here is imported by the web deployment.
"""
import contextlib
import os
import shutil
import socket
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request

import licensing

FROZEN = getattr(sys, 'frozen', False)
LICENSE_REQUIRED = FROZEN or os.environ.get('SAI_LICENSE_CHECK') == '1'


def has_records(path):
    try:
        with contextlib.closing(sqlite3.connect(path)) as db:
            return bool(db.execute(
                'SELECT EXISTS(SELECT 1 FROM app_workorder) OR EXISTS(SELECT 1 FROM app_customer)'
            ).fetchone()[0])
    except sqlite3.Error:
        return False


if FROZEN:
    # A one-file exe unpacks into a temp folder that is deleted on exit, so the
    # database and log must live in a permanent per-user folder instead.
    DATA_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'SAI Calibration')
    os.makedirs(DATA_DIR, exist_ok=True)

    log = open(os.path.join(DATA_DIR, 'app.log'), 'a', encoding='utf-8', buffering=1)
    sys.stdout = sys.stderr = log
    import faulthandler
    faulthandler.enable(log)

    # A db.sqlite3 placed next to the exe is imported, unless real data already exists
    db_path = os.path.join(DATA_DIR, 'db.sqlite3')
    old_db = os.path.join(os.path.dirname(sys.executable), 'db.sqlite3')
    if os.path.exists(old_db) and not has_records(db_path) and has_records(old_db):
        shutil.copy2(old_db, db_path)

    os.environ.setdefault('DATABASE_URL', 'sqlite:///' + db_path.replace('\\', '/'))
    os.environ.setdefault('DEBUG', 'False')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sai_calibrations.settings')

import django

django.setup()

import webview
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from waitress import serve

WINDOW_TITLE = 'CALIBRATION APPLICATION'


def free_port():
    # Pick an unused port so the app never clashes with another server on 8000
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def wait_until_up(url, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except urllib.error.HTTPError:
            return True
        except OSError:
            time.sleep(0.3)
    return False


def note(message):
    print(time.strftime('%Y-%m-%d %H:%M:%S'), message, flush=True)


def open_main_window():
    call_command('migrate', interactive=False, verbosity=0)

    port = free_port()
    url = f'http://127.0.0.1:{port}/'
    threading.Thread(
        target=serve,
        args=(get_wsgi_application(),),
        kwargs={'host': '127.0.0.1', 'port': port, 'threads': 8},
        daemon=True,
    ).start()

    if not wait_until_up(url):
        note('server did not start')
        sys.exit('The calibration server did not start.')
    note(f'server ready at {url}')
    webview.create_window(WINDOW_TITLE, url, maximized=True, min_size=(1100, 700))


class ActivationApi:
    """Called from the activation window's JavaScript."""

    def __init__(self):
        self._window = None

    def activate(self, key):
        ok, message = licensing.activate(key)
        note(f'activation: {message}')
        if not ok:
            return {'ok': False, 'message': message}
        # The main window must exist before the activation window closes, or the app exits
        open_main_window()
        self._window.destroy()
        return {'ok': True, 'message': message}


def main():
    note('starting')
    # Needed for the certificate "Download as PDF" button
    webview.settings['ALLOW_DOWNLOADS'] = True

    ok, message = licensing.check() if LICENSE_REQUIRED else (True, 'licence check skipped')
    note(f'licence: {message or "not activated"}')
    if ok:
        open_main_window()
    else:
        api = ActivationApi()
        api._window = webview.create_window(
            f'Activate - {WINDOW_TITLE}', html=licensing.activation_html(message), js_api=api,
            width=640, height=560, resizable=False,
        )
    webview.start()
    note('window closed')


if __name__ == '__main__':
    main()
