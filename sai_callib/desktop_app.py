"""Run the calibration software in its own desktop window instead of a web browser.

Usage:  python desktop_app.py
Render keeps using manage.py / start.sh; nothing here is imported by the web deployment.
"""
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sai_calibrations.settings')

import django

django.setup()

import webview
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from waitress import serve

WINDOW_TITLE = 'SAI ACCURATE INSTRUMENTS - CALIBRATION'


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


def main():
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
        sys.exit('The calibration server did not start.')

    # Needed for the certificate "Download as PDF" button
    webview.settings['ALLOW_DOWNLOADS'] = True
    webview.create_window(WINDOW_TITLE, url, maximized=True, min_size=(1100, 700))
    webview.start()


if __name__ == '__main__':
    main()
