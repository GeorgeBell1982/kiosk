#!/bin/bash
# Configure one desktop-login autostart entry for the current user.
set -e
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname -- "$SCRIPT_DIR")"

if [ "$(id -u)" -eq 0 ]; then
    echo "Run autostart setup as the desktop user, not root." >&2
    exit 1
fi
if [ ! -f "$PROJECT_DIR/scripts/start_kiosk.sh" ]; then
    echo "Kiosk launcher is missing." >&2
    exit 1
fi
AUTOSTART_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
mkdir -p -- "$AUTOSTART_DIR"
AUTOSTART_FILE="$AUTOSTART_DIR/office-kiosk-browser.desktop"
if [ -e "$AUTOSTART_FILE" ] && ! grep -Fxq 'Name=Office Kiosk Browser' "$AUTOSTART_FILE"; then
    echo "Unrecognized autostart entry preserved: $AUTOSTART_FILE" >&2
    exit 1
fi

# Exec has both desktop-entry string escaping and argument quoting rules.
python3 - "$PROJECT_DIR" "$AUTOSTART_FILE" <<'PY'
from pathlib import Path
import os
import sys
import tempfile
project, destination = map(Path, sys.argv[1:])

def value(text):
    return str(text).replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

def argument(text):
    text = str(text)
    if any(c in text for c in '\n\r\t'):
        raise SystemExit('Control characters in the project path are not supported')
    for char in ('\\', '"', '`', '$'):
        text = text.replace(char, '\\' + char)
    return '"' + value(text).replace('%', '%%') + '"'

content = '\n'.join([
    '[Desktop Entry]', 'Version=1.0', 'Type=Application',
    'Name=Office Kiosk Browser', 'Comment=Start Office Kiosk Browser on desktop login',
    'Exec=/bin/bash ' + argument(project / 'scripts/start_kiosk.sh') + ' --fullscreen',
    'Path=' + value(project), 'Icon=' + value(project / 'icons/home.svg'),
    'Terminal=false', 'Categories=Network;WebBrowser;', 'StartupNotify=false',
    'Hidden=false', 'X-GNOME-Autostart-enabled=true', '',
])
# Validate before replacing an existing entry.
temporary = None
try:
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=destination.parent,
                                     prefix=destination.name + '.', delete=False) as output:
        temporary = Path(output.name)
        output.write(content)
    os.replace(temporary, destination)
finally:
    if temporary is not None and temporary.exists():
        temporary.unlink()
print('Desktop autostart configured: ' + str(destination))
PY

echo "The kiosk will start at the next desktop login."
echo "No systemd service or shell-profile fallback was enabled."
echo "To disable: bash \"$SCRIPT_DIR/manage_autostart.sh\" disable"
