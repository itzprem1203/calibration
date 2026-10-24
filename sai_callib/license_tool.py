"""Create licence keys for the SAI Calibration desktop exe.

Run this only on your own PC. It is never bundled into the exe, and the private key it
uses lives outside the project folder (Desktop\\SAI_License_Keys) so it is never committed.

  python license_tool.py init                                   (once, before the first build)
  python license_tool.py make 3F9A-0C21-7B44-E1D8 --name "ABC Industries"
  python license_tool.py make 3F9A-0C21-7B44-E1D8 --name "ABC Industries" --days 365
"""
import argparse
import csv
import datetime
import os
import re
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from licensing import b64encode, verify

HERE = os.path.dirname(os.path.abspath(__file__))
KEY_DIR = os.environ.get('SAI_LICENSE_KEYS') or os.path.join(os.path.dirname(os.path.dirname(HERE)), 'SAI_License_Keys')
PRIVATE_KEY_FILE = os.path.join(KEY_DIR, 'private_key.pem')
ISSUED_FILE = os.path.join(KEY_DIR, 'issued_licences.csv')


def init():
    if os.path.exists(PRIVATE_KEY_FILE):
        sys.exit(f'A private key already exists at {PRIVATE_KEY_FILE}.\n'
                 'Creating a new one would make every licence you have issued stop working.')

    private_key = Ed25519PrivateKey.generate()
    os.makedirs(KEY_DIR, exist_ok=True)
    with open(PRIVATE_KEY_FILE, 'wb') as f:
        f.write(private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                          serialization.NoEncryption()))

    public_key = b64encode(private_key.public_key().public_bytes(serialization.Encoding.Raw,
                                                                 serialization.PublicFormat.Raw))
    licensing_py = os.path.join(HERE, 'licensing.py')
    with open(licensing_py, encoding='utf-8') as f:
        source = f.read()
    source = re.sub(r"^PUBLIC_KEY = '.*?'", f"PUBLIC_KEY = '{public_key}'", source, count=1, flags=re.M)
    with open(licensing_py, 'w', encoding='utf-8') as f:
        f.write(source)

    print(f'Private key saved to {PRIVATE_KEY_FILE}')
    print('Keep a backup of it. Without it you cannot issue licences for this build.')
    print('licensing.py updated with the public key. Rebuild the exe with .\\build_desktop.ps1')


def make(code, name, days):
    code = code.strip().upper()
    if not re.fullmatch(r'[0-9A-F]{4}(-[0-9A-F]{4}){3}', code):
        sys.exit('Machine Code must look like 3F9A-0C21-7B44-E1D8')
    name = ' '.join(name.split())
    if not name or '|' in name:
        sys.exit('Please give a customer name (without the | character).')
    if not os.path.exists(PRIVATE_KEY_FILE):
        sys.exit(f'No private key at {PRIVATE_KEY_FILE}. Run: python license_tool.py init')

    with open(PRIVATE_KEY_FILE, 'rb') as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    expiry = (datetime.date.today() + datetime.timedelta(days=days)).isoformat() if days else ''
    payload = f'{code}|{name}|{expiry}'.encode()
    key = b64encode(payload) + '.' + b64encode(private_key.sign(payload))

    ok, message = verify(key, code)
    if not ok:
        sys.exit(f'Generated key failed verification ({message}). '
                 'Was licensing.py changed after running init?')

    new_file = not os.path.exists(ISSUED_FILE)
    with open(ISSUED_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(['issued_on', 'customer', 'machine_code', 'expires', 'licence_key'])
        writer.writerow([datetime.date.today().isoformat(), name, code, expiry or 'never', key])

    print(message)
    print()
    print(key)
    print()
    print(f'(Also saved in {ISSUED_FILE})')


def main():
    parser = argparse.ArgumentParser(description='SAI Calibration licence keys')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init', help='create your private key (once)')
    make_parser = sub.add_parser('make', help='create a licence key for a Machine Code')
    make_parser.add_argument('code', help='Machine Code shown on the customer PC')
    make_parser.add_argument('--name', required=True, help='customer name')
    make_parser.add_argument('--days', type=int, default=0, help='licence length in days (default: never expires)')
    args = parser.parse_args()

    if args.command == 'init':
        init()
    else:
        make(args.code, args.name, args.days)


if __name__ == '__main__':
    main()
