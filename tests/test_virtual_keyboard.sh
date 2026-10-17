#!/bin/bash
# Manual Wayland keyboard smoke test. Never installs packages or kills other keyboards.

set -u

if [ -z "${WAYLAND_DISPLAY:-}" ] && [ "${XDG_SESSION_TYPE:-}" != "wayland" ]; then
    echo "wvkbd requires a Wayland desktop with a compatible compositor."
    echo "For X11, use an X11 keyboard such as Onboard."
    exit 1
fi

if ! command -v wvkbd-mobintl >/dev/null 2>&1; then
    echo "wvkbd-mobintl is not installed. Install it with:"
    echo "  sudo apt update && sudo apt install wvkbd"
    exit 1
fi

keyboard_pid=""
cleanup() {
    if [ -n "$keyboard_pid" ]; then
        kill "$keyboard_pid" 2>/dev/null || true
        for attempt in {1..10}; do
            kill -0 "$keyboard_pid" 2>/dev/null || break
            sleep 0.1
        done
        kill -KILL "$keyboard_pid" 2>/dev/null || true
        wait "$keyboard_pid" 2>/dev/null || true
    fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "Starting a 180px keyboard for five seconds."
echo "Check visibility and typing in an already-focused text field."
wvkbd-mobintl -H 180 -L 180 &
keyboard_pid=$!
sleep 1
if ! kill -0 "$keyboard_pid" 2>/dev/null; then
    wait "$keyboard_pid" 2>/dev/null || true
    keyboard_pid=""
    echo "Keyboard exited early; check the compositor error above."
    exit 1
fi
sleep 5
if ! kill -0 "$keyboard_pid" 2>/dev/null; then
    wait "$keyboard_pid" 2>/dev/null || true
    keyboard_pid=""
    echo "Keyboard stopped during the test."
    exit 1
fi
echo "Test complete. Stopping only the keyboard started by this script."
