"""Run the calibration software in its own desktop window instead of a web browser.

Usage:  python desktop_app.py
Render keeps using manage.py / start.sh; nothing here is imported by the web deployment.
"""
import os
import shutil
import socket
import sys
import threading
import time
import urllib.error
import urllib.request

FROZEN = getattr(sys, 'frozen', False)

if FROZEN:
    # A one-file exe unpacks into a temp folder that is deleted on exit, so the
    # database and log must live in a permanent per-user folder instead.
    DATA_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'SAI Calibration')
    os.makedirs(DATA_DIR, exist_ok=True)

    log = open(os.path.join(DATA_DIR, 'app.log'), 'a', encoding='utf-8', buffering=1)
    sys.stdout = sys.stderr = log
    import faulthandler
    faulthandler.enable(log)

    db_path = os.path.join(DATA_DIR, 'db.sqlite3')
    old_db = os.path.join(os.path.dirname(sys.executable), 'db.sqlite3')
    if not os.path.exists(db_path) and os.path.exists(old_db):
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


def main():
    note('starting')
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

    # Needed for the certificate "Download as PDF" button
    webview.settings['ALLOW_DOWNLOADS'] = True
    webview.create_window(WINDOW_TITLE, url, maximized=True, min_size=(1100, 700))
    webview.start()
    note('window closed')


if __name__ == '__main__':
    main()
