# Virtual Keyboard and Touchscreen Behavior

The Raspberry Pi keyboard button starts `wvkbd-mobintl` in a Wayland desktop.
The compositor must support the wlr-layer-shell and virtual-keyboard protocols.
X11 sessions display an explanation instead of attempting to run a Wayland
keyboard; use an X11 keyboard such as Onboard for those desktops.

## Installation

```bash
sudo apt update
sudo apt install wvkbd
```

For source builds and compositor requirements, follow the
[upstream wvkbd instructions](https://github.com/jjsullivan5196/wvkbd).

## Using the keyboard

1. Tap a text field in the browser.
2. Tap the keyboard button. The text field keeps focus.
3. Type, then tap the keyboard button again to close it.

The button turns orange after the process starts and gray when it stops. Starting
and stopping are asynchronous, so taps do not block browser interaction. Rapid
taps can cancel startup without launching a second process.

The browser owns its keyboard process. It does not scan for or stop keyboards
started by other applications, including at startup. Unexpected exits reset the
button and report a short diagnostic. Closing the browser stops its keyboard;
a process that ignores normal termination is killed after one second.

## Fullscreen and layout

When the keyboard starts from fullscreen, the browser temporarily maximizes so
that the compositor can resize it around the keyboard's reserved screen area.
Fullscreen is restored when the keyboard exits. An explicit fullscreen toggle
while typing overrides that automatic restoration. Windowed sessions keep their
window state.

The toolbar uses expanding layouts and buttons at least 44 logical pixels high
and wide. It fits an 800px-wide display and adapts when resized. Toolbar taps
preserve page focus; physical Tab navigation remains available. F11, F12, and
Ctrl+R also work while a page has focus.

The keyboard command is:

```bash
wvkbd-mobintl -H 180 -L 180
```

`-H` sets the portrait height and `-L` sets the landscape height. wvkbd handles
orientation and bottom anchoring itself. The application uses neither the
unsupported `--anchor`/`--layer` options nor `wmctrl` window activation.

## Troubleshooting and testing

If startup fails, check that you are in a supported Wayland desktop and that
`wvkbd-mobintl` is installed. Run the command above in a terminal to see its
compositor diagnostics. Do not disable browser security settings to troubleshoot
the keyboard.

The manual smoke test runs a keyboard for five seconds and stops only that child:

```bash
bash tests/test_virtual_keyboard.sh
```

It does not install packages or kill existing keyboards. To check the compositor,
tap an input field before launching the test, then verify actual key delivery.

Automated headless tests cover process ownership and failures, rapid taps,
fullscreen restoration, toolbar geometry, text-field focus, and keyboard shortcuts:

```bash
python -m unittest discover -s tests -p test_touch_keyboard.py -v
```

They use real child processes in place of wvkbd. Actual touch events, compositor
resizing, keyboard positioning, and key delivery from wvkbd still require a
Raspberry Pi touchscreen session.
